/* Host-only parser tests: no controller or device access. */
#include <assert.h>
#include <string.h>
#include "../ufs_response.h"

int main(void)
{
	uint8_t r[512] = {0};
	struct ufs_response d;
	r[0] = 0x21; r[6] = 1; r[7] = 2; r[33] = 18;
	for (unsigned code = 0x70; code <= 0x73; code++) {
		memset(r + 34, 0, 18);
		r[34] = code | 0x80;
		if (code < 0x72) {
			r[36] = 0xf6; r[46] = 0x29; r[47] = 3;
		} else {
			r[35] = 0xf6; r[36] = 0x29; r[37] = 3;
		}
		ufs_decode_response(r, sizeof(r), &d);
		assert(d.valid && d.transaction == 0x21 && d.response == 1 && d.status == 2);
		assert(d.code == code && d.has_key && d.has_asc);
		assert(d.key == 6 && d.asc == 0x29 && d.ascq == 3);
	}
	r[34] = 0x70; r[33] = 13;
	ufs_decode_response(r, sizeof(r), &d);
	assert(d.has_key && !d.has_asc);
	r[34] = 0x72; r[33] = 3;
	ufs_decode_response(r, sizeof(r), &d);
	assert(d.has_key && !d.has_asc);
	r[33] = 1;
	ufs_decode_response(r, sizeof(r), &d);
	assert(!d.has_key && !d.has_asc);
	r[34] = 0x55; r[33] = 18;
	ufs_decode_response(r, sizeof(r), &d);
	assert(d.code == 0x55 && !d.has_key && d.sense[0] == 0x55);
	r[33] = 0;
	ufs_decode_response(r, sizeof(r), &d);
	assert(d.valid && !d.sense_len && !d.has_key);
	r[32] = 1; r[33] = 222; /* 478: full available payload, cap copy at 18 */
	ufs_decode_response(r, sizeof(r), &d);
	assert(d.valid && d.sense_data_len == 478 && d.sense_len == 18);
	r[33] = 223;
	ufs_decode_response(r, sizeof(r), &d);
	assert(!d.valid && !d.sense_len);
	r[0] = 0x3f; r[32] = 0; r[33] = 18;
	ufs_decode_response(r, sizeof(r), &d);
	assert(!d.valid && !d.sense_len);
	/* A small actual allocation checks the short-header guard. */
	uint8_t short_response[8] = {0};
	ufs_decode_response(short_response, sizeof(short_response), &d);
	assert(!d.valid && !d.sense_len);
	return 0;
}
