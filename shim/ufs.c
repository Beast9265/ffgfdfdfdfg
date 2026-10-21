/*
 * Milestone 5 probe: can we talk to the internal UFS that ABL booted from?
 *
 * Runs with the MMU off (all memory Device, so DMA is coherent with no cache
 * maintenance). Dumps the UFSHCI registers ABL left behind and, if the host
 * is enabled and the link is up, points the transfer request list at our own
 * buffers and issues SCSI probes on LUN 0. Nothing is ever
 * written to storage: there is no SCSI WRITE in this file. MARBLE alone
 * reads fDeviceInit, then permits one gated device-WLUN ACTIVE command.
 *
 * Register layout and descriptor formats: JEDEC UFSHCI (JESD223).
 */
#include <stdint.h>
#include "console.h"
#include "ufs.h"
#include "ufs_response.h"

#include "board.h"

#define REG_CAP		0x00
#define REG_VER		0x08
#define REG_IS		0x20
#define REG_HCS		0x30
#define REG_HCE		0x34
#define REG_UTRLBA	0x50
#define REG_UTRLBAU	0x54
#define REG_UTRLDBR	0x58
#define REG_UTRLCLR	0x5c
#define REG_UTRLRSR	0x60

#define HCS_DP		(1u << 0)
#define HCS_UTRLRDY	(1u << 1)
#define HCS_UCRDY	(1u << 3)

#define BLOCK		4096u

static inline uint32_t ufs_rd(uint32_t off) { return *(volatile uint32_t *)(UFS_BASE + off); }
static inline void ufs_wr(uint32_t off, uint32_t v) { *(volatile uint32_t *)(UFS_BASE + off) = v; }

/* UTP transfer request descriptor (32 bytes). */
struct utrd {
	uint32_t dw0;		/* [31:28] CT, [26:25] DD, [24] I */
	uint32_t dw1;
	uint32_t dw2;		/* [7:0] OCS */
	uint32_t dw3;
	uint32_t ucdba;		/* command descriptor base, 128-byte aligned */
	uint32_t ucdbau;
	uint32_t resp;		/* [31:16] response UPIU offset, [15:0] length (DWORDs) */
	uint32_t prdt;		/* [31:16] PRDT offset, [15:0] entries (DWORDs/entries) */
};

/* UTP command descriptor: command UPIU, response UPIU, PRDT. */
struct ucd {
	uint8_t cmd[512];
	uint8_t resp[512];
	struct {
		uint32_t addr_lo, addr_hi, rsvd, dbc;	/* dbc = byte count - 1 */
	} prdt[1];
};

static struct utrd utrl[32] __attribute__((aligned(1024)));
static struct ucd ucd __attribute__((aligned(128)));
static uint8_t data[2 * BLOCK] __attribute__((aligned(4096)));

static uint64_t ticks(void)
{
	uint64_t t;
	__asm__ volatile("isb; mrs %0, cntvct_el0" : "=r"(t));
	return t;
}

static void zero(void *p, unsigned n)
{
	volatile uint8_t *b = p;
	for (unsigned i = 0; i < n; i++)
		b[i] = 0;
}

static uint32_t be32(const uint8_t *p)
{
	return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3];
}

#ifdef SHIM_MARBLE
/* Standard UPIU header + query OSF, as in Linux scsi_bsg_ufs.h.
 * Byte arrays retain wire endianness and avoid alignment/padding ambiguity.
 */
struct query_header {
	uint8_t transaction, flags, lun, tag;
	uint8_t iid_command_set, function, response, status;
	uint8_t ehs_length, device_info, data_length[2];
};
struct query_osf {
	uint8_t opcode, idn, index, selector;
	uint8_t reserved_osf[2], length[2], value[4], reserved[8];
};
struct query_upiu {
	struct query_header header;
	struct query_osf osf;
};
_Static_assert(sizeof(struct query_header) == 12, "UPIU header");
_Static_assert(sizeof(struct query_osf) == 20, "query OSF");
_Static_assert(sizeof(struct query_upiu) == 32, "query UPIU");
_Static_assert(__builtin_offsetof(struct query_upiu, osf.value) == 20, "query value");

#define QUERY_REQ 0x16
#define QUERY_RSP 0x36
#define READ_FLAG 0x05
#define FDEVICEINIT 0x01

struct query_diag {
	uint32_t ocs, value;
	uint8_t transaction, response, reserved7;
};

/* Every device-management doorbell revalidates ownership and idle state.
 * A timed-out slot must be idle before any retry can reuse its DMA buffers.
 */
static int dev_list_ready(void)
{
	uintptr_t list = (uintptr_t)utrl;
	return ufs_rd(REG_UTRLBA) == (uint32_t)list &&
	    ufs_rd(REG_UTRLBAU) == (uint32_t)(list >> 32) &&
	    (ufs_rd(REG_UTRLRSR) & 1) && !ufs_rd(REG_UTRLDBR);
}

static uint32_t dev_submit(uint64_t start, uint64_t budget)
{
	if (!dev_list_ready())
		return 6;
	if (ticks() - start >= budget)
		return 1;
	uintptr_t pa = (uintptr_t)&ucd;
	utrl[0].dw0 = (1u << 28) | (1u << 24); /* storage, no data */
	utrl[0].dw2 = 0x0f;
	utrl[0].ucdba = (uint32_t)pa;
	utrl[0].ucdbau = (uint32_t)(pa >> 32);
	utrl[0].resp = (512u / 4) << 16 | (512u / 4);
	/* PRDT remains entirely zero. */
	if (ucd.cmd[0] == QUERY_REQ) {
		/* Wire bytes in BE groups; descriptor fields are native LE dwords. */
		for (unsigned i = 0; i < 32; i += 8)
			con_hex2("FDEV REQ", "a=", be32(ucd.cmd + i),
			    "b=", be32(ucd.cmd + i + 4));
		con_hex2("FDEV UTRD", "DW0=", utrl[0].dw0, "DW1=", utrl[0].dw1);
		con_hex2("FDEV UTRD", "DW2=", utrl[0].dw2, "DW3=", utrl[0].dw3);
		con_hex2("FDEV UTRD", "UCD lo=", utrl[0].ucdba, "hi=", utrl[0].ucdbau);
		con_hex2("FDEV UTRD", "resp off/len=", utrl[0].resp,
		    "PRDT off/len=", utrl[0].prdt);
	}
	__asm__ volatile("dsb sy" ::: "memory");
	ufs_wr(REG_UTRLDBR, 1);
	while (ufs_rd(REG_UTRLDBR) & 1) {
		if (ticks() - start >= budget) {
			ufs_wr(REG_UTRLCLR, ~1u);
			return 1;
		}
	}
	__asm__ volatile("dsb sy" ::: "memory");
	return 0;
}

static int ufs_verify_dev_init(uint64_t freq)
{
	static uint8_t tag;
	for (unsigned attempt = 0; attempt < 10; attempt++) {
		con_hex2("UFS NOP", "try=", attempt, "", 0);
		/* Never overwrite buffers while a timed-out request is still active. */
		uint32_t rc = 6, ocs = 0x0f;
		uint8_t sent = tag;
		if (dev_list_ready()) {
			zero(&utrl[0], sizeof(utrl[0]));
			zero(&ucd, sizeof(ucd));
			/* NOP OUT: byte 0 = 0x00; only byte 3 (task tag) is nonzero. */
			ucd.cmd[3] = sent = ++tag;
			rc = dev_submit(ticks(), freq / 20); /* 50 ms */
			ocs = utrl[0].dw2 & 0xff;
			if (!rc && ocs)
				rc = 2;
			if (!rc && (ucd.resp[0] != 0x20 || ucd.resp[3] != sent))
				rc = 3;
		}
		con_hex2("NOP", "rc=", rc, "ocs=", ocs);
		con_hex2("NOP", "txn=", ucd.resp[0], "tag=", ucd.resp[3]);
		if (!rc) {
			con_str("UFS NOP", "ready");
			return 1;
		}
		con_hex2("NOP", "sent tag=", sent, "got tag=", ucd.resp[3]);
		for (unsigned i = 0; i < 12; i += 4)
			con_hex2("NOP HDR", "offset=", i, "bytes=", be32(ucd.resp + i));
		if (rc == 6 || !dev_list_ready())
			break;
	}
	con_str("UFS NOP", "failed: stop");
	return 0;
}

/* Only READ_FLAG fDeviceInit is permitted. No device-management write API.
 * Caller has completed takeover; recheck the list before every doorbell.
 * All transfers share the caller's absolute 1500 ms deadline.
 */
static uint32_t query_flag(uint8_t opcode, unsigned *value,
    struct query_diag *d, uint64_t start, uint64_t budget)
{
	static uint8_t tag;
	zero(d, sizeof(*d));
	d->ocs = 0x0f;
	if (opcode != READ_FLAG)
		return 5;
	uintptr_t list = (uintptr_t)utrl;
	if (ufs_rd(REG_UTRLBA) != (uint32_t)list ||
	    ufs_rd(REG_UTRLBAU) != (uint32_t)(list >> 32) ||
	    !(ufs_rd(REG_UTRLRSR) & 1) || ufs_rd(REG_UTRLDBR))
		return 6;
	if (ticks() - start >= budget)
		return 1;
	zero(&utrl[0], sizeof(utrl[0]));
	zero(&ucd, sizeof(ucd));
	struct query_upiu *q = (void *)ucd.cmd;
	q->header.transaction = QUERY_REQ;
	q->header.tag = ++tag;
	q->header.function = 0x01;
	q->osf.opcode = opcode;
	q->osf.idn = FDEVICEINIT;
	uint32_t rc = dev_submit(start, budget);
	if (rc) {
		d->ocs = utrl[0].dw2 & 0xff;
		return rc;
	}
	const struct query_upiu *r = (const void *)ucd.resp;
	d->ocs = utrl[0].dw2 & 0xff;
	d->transaction = r->header.transaction;
	/* Query response/result is header byte 6; byte 7 is reserved. */
	d->response = r->header.response;
	d->reserved7 = r->header.status;
	d->value = be32(r->osf.value);
	if (d->ocs)
		return 2;
	if (d->transaction != QUERY_RSP || r->header.tag != q->header.tag)
		return 3;
	if (d->response || d->reserved7)
		return 4;
	if (r->osf.opcode != opcode || r->osf.idn != FDEVICEINIT ||
	    r->osf.index || r->osf.selector || r->header.ehs_length ||
	    r->header.data_length[0] || r->header.data_length[1])
		return 3;
	*value = d->value & 1;
	return ticks() - start >= budget ? 1 : 0;
}

static const char *query_result_name(uint8_t result)
{
	switch (result) {
	case 0x00: return "SUCCESS";
	case 0xf6: return "NOT_READABLE";
	case 0xf7: return "NOT_WRITEABLE";
	case 0xf8: return "ALREADY_WRITTEN";
	case 0xf9: return "INVALID_LENGTH";
	case 0xfa: return "INVALID_VALUE";
	case 0xfb: return "INVALID_SELECTOR";
	case 0xfc: return "INVALID_INDEX";
	case 0xfd: return "INVALID_IDN";
	case 0xfe: return "INVALID_OPCODE";
	case 0xff: return "GENERAL FAILURE";
	default: return "unknown result";
	}
}

static void show_query(const char *label, uint32_t rc, const struct query_diag *d)
{
	con_hex2(label, "rc=", rc, "ocs=", d->ocs);
	con_hex2("Q", "txn=", d->transaction, "result=", d->response);
	con_hex2("Q", "byte7=", d->reserved7, "value=", d->value);
	if (rc) {
		con_str("Q result", query_result_name(d->response));
		/* Complete fixed header/OSF, including echoed opcode/IDN. */
		for (unsigned i = 0; i < 32; i += 8)
			con_hex2("Q RAW", "a=", be32(ucd.resp + i),
			    "b=", be32(ucd.resp + i + 4));
	}
}

static int ufs_complete_dev_init(void)
{
	uint64_t freq;
	__asm__ volatile("mrs %0, cntfrq_el0" : "=r"(freq));
	con_str("UFS INIT", "begin");
	if (freq < 1000000) {
		con_str("INIT", "invalid timer frequency: stop");
		return 0;
	}
	if (!ufs_verify_dev_init(freq))
		return 0;
	uint64_t start = ticks(), budget = freq * 3 / 2;
	unsigned value = 1;
	struct query_diag d;
	uint32_t rc = query_flag(READ_FLAG, &value, &d, start, budget);
	show_query("FDEV", rc, &d);
	if (rc) {
		con_str("FDEV", rc == 1 ? "timeout" : "query error: stop");
		return 0;
	}
	con_str("FDEV", value ? "flag=1" : "flag=0");
	con_str("FDEV", value ? "already set" : "already clear");
	if (!value)
		return 1;
	for (;;) {
		uint64_t delay = ticks();
		while (ticks() - delay < freq / 1000 && ticks() - start < budget)
			;
		if (ticks() - start >= budget) {
			con_str("FDEV", "timeout");
			return 0;
		}
		rc = query_flag(READ_FLAG, &value, &d, start, budget);
		if (rc) {
			show_query("FDEV", rc, &d);
			con_str("FDEV", rc == 1 ? "timeout" : "query error: stop");
			return 0;
		}
		if (!value) {
			show_query("FDEV", rc, &d);
			con_str("FDEV", "flag=0");
			con_str("FDEV", "ready");
			return 1;
		}
	}
}
#endif

/*
 * Issue one SCSI command (read direction or no data) in slot 0.
 * Returns 0 on success, otherwise a code describing the failure stage.
 */
static uint32_t scsi_timed(uint8_t lun, const uint8_t *cdb, unsigned cdb_len, void *buf, uint32_t len,
    uint32_t *ocs_out, uint32_t *status_out, struct ufs_response *diag,
    uint64_t start, uint64_t budget)
{
	static uint8_t tag;
	zero(diag, sizeof(*diag));
	*ocs_out = 0x0f;
	*status_out = 0;
#ifdef SHIM_MARBLE
	if (!dev_list_ready())
		return 6;
#endif
	zero(&utrl[0], sizeof(utrl[0]));
	zero(&ucd, sizeof(ucd));

	/* Command UPIU: header (12 bytes), expected length, CDB. */
	ucd.cmd[0] = 0x01;			/* transaction type: COMMAND */
	ucd.cmd[1] = len ? 0x40 : 0x00;		/* flags: R (data in) */
	ucd.cmd[2] = lun;
	ucd.cmd[3] = ++tag;
	ucd.cmd[12] = len >> 24;
	ucd.cmd[13] = len >> 16;
	ucd.cmd[14] = len >> 8;
	ucd.cmd[15] = len;
	for (unsigned i = 0; i < cdb_len; i++)
		ucd.cmd[16 + i] = cdb[i];

	uintptr_t ucd_pa = (uintptr_t)&ucd;
	utrl[0].dw0 = (1u << 28) | ((len ? 2u : 0u) << 25) | (1u << 24);	/* UFS storage, dev->host */
	utrl[0].dw2 = 0x0f;			/* OCS: invalid until the host updates it */
	utrl[0].ucdba = (uint32_t)ucd_pa;
	utrl[0].ucdbau = (uint32_t)(ucd_pa >> 32);
	utrl[0].resp = (512u / 4) << 16 | (512u / 4);
	if (len) {
		uintptr_t buf_pa = (uintptr_t)buf;
		ucd.prdt[0].addr_lo = (uint32_t)buf_pa;
		ucd.prdt[0].addr_hi = (uint32_t)(buf_pa >> 32);
		ucd.prdt[0].dbc = len - 1;
		utrl[0].prdt = (1024u / 4) << 16 | 1;
	}
	__asm__ volatile("dsb sy" ::: "memory");

#ifdef SHIM_MARBLE
	if (!dev_list_ready())
		return 6;
#endif
	if (ticks() - start >= budget)
		return 1;
	ufs_wr(REG_UTRLDBR, 1);
	while (ufs_rd(REG_UTRLDBR) & 1) {
		if (ticks() - start >= budget) {	/* shared transfer deadline */
			ufs_wr(REG_UTRLCLR, ~1u);	/* clear slot 0 (write 0 to the bit) */
			return 1;			/* timeout */
		}
	}
	__asm__ volatile("dsb sy" ::: "memory");
	ufs_decode_response(ucd.resp, sizeof(ucd.resp), diag);
	*ocs_out = utrl[0].dw2 & 0xff;
	*status_out = ucd.resp[7];		/* SCSI status in the response UPIU */
	if (*ocs_out)
		return 2;
	if (ucd.resp[0] != 0x21)		/* RESPONSE UPIU */
		return 3;
	return *status_out ? 4 : 0;
}

static uint32_t scsi(uint8_t lun, const uint8_t *cdb, unsigned cdb_len, void *buf, uint32_t len,
    uint32_t *ocs_out, uint32_t *status_out, struct ufs_response *diag)
{
	return scsi_timed(lun, cdb, cdb_len, buf, len, ocs_out, status_out, diag,
	    ticks(), 19200000); /* existing one-second transfer bound */
}

/* Compact byte output keeps the diagnostics within the 43-column screen. */
static char *hexbyte(char *p, uint8_t v)
{
	static const char hex[] = "0123456789ABCDEF";
	*p++ = hex[v >> 4];
	*p++ = hex[v & 15];
	return p;
}

static void show_response(const struct ufs_response *d)
{
	char meta[] = "t=00 r=00 len=0000";
	hexbyte(meta + 2, d->transaction);
	hexbyte(meta + 7, d->response);
	hexbyte(meta + 14, d->sense_data_len >> 8);
	hexbyte(meta + 16, d->sense_data_len);
	con_str("UPIU", meta);
	if (!d->valid) {
		con_str("SNS", "invalid/unavailable response sense");
		return;
	}
	if (!d->sense_len) {
		con_str("SNS", "sense len=0");
		return;
	}
	if (d->has_key && d->has_asc) {
		char text[] = "k=00 asc=00 q=00";
		hexbyte(text + 2, d->key);
		hexbyte(text + 9, d->asc);
		hexbyte(text + 14, d->ascq);
		con_str("SNS", text);
		return;
	}
	/* Unknown or short format: include response code and all captured bytes. */
	con_hex2("SNS", "code=", d->code, 0, 0);
	for (unsigned i = 0; i < d->sense_len; i += 9) {
		char raw[27], *p = raw;
		for (unsigned j = i; j < d->sense_len && j < i + 9; j++) {
			if (j != i)
				*p++ = ' ';
			p = hexbyte(p, d->sense[j]);
		}
		*p = 0;
		con_str("RAW", raw);
	}
}

#ifdef SHIM_MARBLE
static int lun0_initializing(uint32_t rc, uint32_t ocs, uint32_t st,
    const struct ufs_response *d)
{
	return rc == 4 && ocs == 0 && st == 2 && d->valid &&
	    d->has_key && d->has_asc && d->key == 2 && d->asc == 4 && d->ascq == 2;
}

static int lun0_ready(void)
{
	static const uint8_t tur[6] = { 0x00 };
	static const uint8_t devact[6] = { 0x1b, 0, 0, 0, 0x10, 0 };
	uint32_t ocs, st, rc;
	struct ufs_response d;
	rc = scsi(0, tur, sizeof(tur), 0, 0, &ocs, &st, &d);
	con_hex2("TUR0", "rc=", rc, "ocs/st=", ocs << 8 | st);
	if (!rc) {
		con_str("LUN0", "READY");
		return 1;
	}
	show_response(&d);
	if (!lun0_initializing(rc, ocs, st, &d))
		return 0;
	/* Linux UFS whole-device ACTIVE power condition; no data/PRDT. */
	con_str("DEVACT", "lun=D0");
	con_str("CDB", "1B0000001000");
	rc = scsi(0xd0, devact, sizeof(devact), 0, 0, &ocs, &st, &d);
	con_hex2("DEVACT", "rc=", rc, "ocs/st=", ocs << 8 | st);
	if (rc) {
		show_response(&d);
		return 0;
	}
	uint64_t freq;
	__asm__ volatile("mrs %0, cntfrq_el0" : "=r"(freq));
	con_str("DEVACT", "ready");
	uint64_t begin = ticks(), budget = freq * 5;
	/* Poll immediately and at 100ms offsets; transfers share the 5s deadline. */
	for (unsigned i = 0; i < 50; i++) {
		while (ticks() - begin < (freq / 10) * i)
			;
		if (ticks() - begin >= budget)
			break;
		rc = scsi_timed(0, tur, sizeof(tur), 0, 0, &ocs, &st, &d,
		    begin, budget);
		int initializing = lun0_initializing(rc, ocs, st, &d);
		if (i == 0 || i == 49 || !initializing) {
			char label[] = "TUR+00";
			label[4] = '0' + i / 10;
			label[5] = '0' + i % 10;
			con_hex2(label, "rc=", rc, "ocs/st=", ocs << 8 | st);
			if (rc)
				show_response(&d);
		}
		if (!rc) {
			con_str("LUN0", "READY");
			return 1;
		}
		if (!initializing)
			return 0;
	}
	while (ticks() - begin < budget)
		;
	con_str("LUN0", "still not ready");
	return 0;
}
#endif

static uint32_t read_blocks(uint32_t lba, uint32_t count, void *buf)
{
	uint8_t cdb[10] = { 0x28, 0, lba >> 24, lba >> 16, lba >> 8, lba, 0, count >> 8, count, 0 };
	uint32_t ocs, st;
	struct ufs_response diag;
	return scsi(0, cdb, sizeof(cdb), buf, count * BLOCK, &ocs, &st, &diag);
}

static uint64_t le64(const uint8_t *p)
{
	uint64_t v = 0;
	for (int i = 7; i >= 0; i--)
		v = v << 8 | p[i];
	return v;
}

/* Name the filesystem whose superblock starts at block lba (f2fs/ext4). */
static const char *fs_type(uint32_t lba)
{
	if (read_blocks(lba, 1, data))
		return "read error";
	const uint8_t *sb = data + 1024;
	if (sb[0] == 0x10 && sb[1] == 0x20 && sb[2] == 0xf5 && sb[3] == 0xf2)
		return "f2fs";
	if (sb[56] == 0x53 && sb[57] == 0xef)
		return "ext4";
	return "other";
}

/* One line per GPT entry of at least 64 MiB: name, first LBA, size in MiB (4K blocks). */
static void list_partitions(uint32_t entry_lba, uint32_t nent)
{
	static uint8_t ents[128 * 128] __attribute__((aligned(4096)));
	uint32_t blocks = (nent * 128 + BLOCK - 1) / BLOCK;
	if (read_blocks(entry_lba, blocks, ents)) {
		con_str("UFS PART", "read error");
		return;
	}
	for (uint32_t i = 0; i < nent; i++) {
		const uint8_t *e = ents + i * 128;
		uint64_t first = le64(e + 32), last = le64(e + 40);
		if (!first)
			continue;
		char name[17];
		for (int c = 0; c < 16; c++) {
			uint8_t ch = e[56 + 2 * c];
			name[c] = (ch >= 32 && ch < 127) ? ch : (ch ? '?' : 0);
		}
		name[16] = 0;
		if (((last - first + 1) >> 8) < 64)	/* keep the screen to the big ones */
			continue;
		con_hex2(name, "lba=", (uint32_t)first, "MiB=", (uint32_t)((last - first + 1) >> 8));
		if (!__builtin_strcmp(name, "userdata") || !__builtin_strcmp(name, "cust") ||
		    !__builtin_strcmp(name, "cache"))
			con_str(" fs", fs_type((uint32_t)first));
	}
}

void test_ufs(void)
{
	con_str("UFS", "milestone 5 probe (read-only)");
	uint32_t cap = ufs_rd(REG_CAP), hcs = ufs_rd(REG_HCS), hce = ufs_rd(REG_HCE);
	con_hex2("UFS", "ver=", ufs_rd(REG_VER), "cap=", cap);
	con_hex2("UFS", "hce=", hce, "hcs=", hcs);
	con_hex2("UFS", "is=", ufs_rd(REG_IS), "rsr=", ufs_rd(REG_UTRLRSR));
	con_hex2("UFS", "utrlba=", ufs_rd(REG_UTRLBA), "hi=", ufs_rd(REG_UTRLBAU));
	con_hex2("UFS", "dbr=", ufs_rd(REG_UTRLDBR), "nutrs=", (cap & 0x1f) + 1);

	if (!(hce & 1) || !(hcs & HCS_DP) || !(hcs & HCS_UTRLRDY)) {
		con_str("UFS", "host not enabled/ready: stop");
		return;
	}
	if (ufs_rd(REG_UTRLDBR)) {
		con_str("UFS", "requests outstanding: stop");
		return;
	}

	/* Take over the transfer request list: stop, point at ours, run. */
	ufs_wr(REG_UTRLRSR, 0);
	uintptr_t list = (uintptr_t)utrl;
	ufs_wr(REG_UTRLBA, (uint32_t)list);
	ufs_wr(REG_UTRLBAU, (uint32_t)(list >> 32));
	ufs_wr(REG_UTRLRSR, 1);
	con_hex2("UFS", "ours=", (uint32_t)list, "rsr=", ufs_rd(REG_UTRLRSR));
	/*
	 * Never ring a doorbell unless the host really uses our list: otherwise
	 * it would execute whatever ABL left in its own slot 0 (maybe a write).
	 */
	if (ufs_rd(REG_UTRLBA) != (uint32_t)list || ufs_rd(REG_UTRLBAU) != (uint32_t)(list >> 32) ||
	    !(ufs_rd(REG_UTRLRSR) & 1)) {
		con_str("UFS", "list base not taken: stop");
		return;
	}

#ifdef SHIM_MARBLE
	if (!ufs_complete_dev_init())
		return;
#endif

	uint32_t ocs = 0, st = 0, rc;
	struct ufs_response diag;
#ifdef SHIM_MARBLE
	if (!lun0_ready())
		return;
#else
	static const uint8_t tur[6] = { 0x00 };
	/* A first command may report a unit attention; retry a few times. */
	for (int i = 0; i < 3; i++) {
		rc = scsi(0, tur, sizeof(tur), 0, 0, &ocs, &st, &diag);
		const char *label = i == 0 ? "TUR0" : i == 1 ? "TUR1" : "TUR2";
		con_hex2(label, "rc=", rc, "ocs/st=", ocs << 8 | st);
		if (rc)
			show_response(&diag);
		if (!rc)
			break;
	}

#endif

	static const uint8_t cap10[10] = { 0x25 };	/* READ CAPACITY(10) */
	rc = scsi(0, cap10, sizeof(cap10), data, 8, &ocs, &st, &diag);
	con_hex2("UFS CAP", "rc=", rc, "ocs/st=", ocs << 8 | st);
	if (rc)
		show_response(&diag);
	if (!rc)
		con_hex2("UFS LUN0", "lastlba=", be32(data), "blk=", be32(data + 4));

	/* READ(10) LBA 0, 2 blocks: protective MBR and the GPT header. */
	static const uint8_t rd10[10] = { 0x28, 0, 0, 0, 0, 0, 0, 0, 2, 0 };
	rc = scsi(0, rd10, sizeof(rd10), data, 2 * BLOCK, &ocs, &st, &diag);
	con_hex2("UFS READ", "rc=", rc, "ocs/st=", ocs << 8 | st);
	if (rc)
		show_response(&diag);
	if (rc)
		return;
	con_hex2("UFS MBR", "sig=", data[510] | data[511] << 8, "type=", data[450]);
	const uint8_t *gpt = data + BLOCK;
	char sig[9];
	for (int i = 0; i < 8; i++)
		sig[i] = (gpt[i] >= 32 && gpt[i] < 127) ? gpt[i] : '.';
	sig[8] = 0;
	con_str("UFS GPT", sig);
	uint32_t nent = gpt[80] | gpt[81] << 8 | gpt[82] << 16, esz = gpt[84] | gpt[85] << 8;
	uint32_t elba = gpt[72] | gpt[73] << 8;
	con_hex2("UFS GPT", "entries=", nent, "lba=", elba);
	if (esz != 128 || nent > 128)
		return;
	list_partitions(elba, nent);
}
