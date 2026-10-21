#pragma once
#include <stdint.h>

/* RESPONSE UPIU: 12-byte header, residual(4), reserved(16), BE16 length. */
struct ufs_response {
	uint8_t transaction, response, status;
	uint16_t sense_data_len;
	uint8_t sense[18], sense_len, valid;
	uint8_t code, key, asc, ascq, has_key, has_asc;
};

static inline void ufs_decode_response(const uint8_t *r, unsigned size, struct ufs_response *d)
{
	volatile uint8_t *bytes = (volatile uint8_t *)d;
	for (unsigned i = 0; i < sizeof(*d); i++)
		bytes[i] = 0;
	if (size < 34)
		return;
	d->transaction = r[0];
	d->response = r[6];
	d->status = r[7];
	d->sense_data_len = (uint16_t)r[32] << 8 | r[33];
	if (d->transaction != 0x21 || d->sense_data_len > size - 34)
		return;
	d->valid = 1;
	d->sense_len = d->sense_data_len > 18 ? 18 : d->sense_data_len;
	for (unsigned i = 0; i < d->sense_len; i++)
		d->sense[i] = r[34 + i];
	if (!d->sense_len)
		return;
	d->code = d->sense[0] & 0x7f;
	if (d->code == 0x70 || d->code == 0x71) {
		if (d->sense_len >= 3) {
			d->key = d->sense[2] & 0x0f;
			d->has_key = 1;
		}
		if (d->sense_len >= 14) {
			d->asc = d->sense[12];
			d->ascq = d->sense[13];
			d->has_asc = 1;
		}
	} else if (d->code == 0x72 || d->code == 0x73) {
		if (d->sense_len >= 2) {
			d->key = d->sense[1] & 0x0f;
			d->has_key = 1;
		}
		if (d->sense_len >= 4) {
			d->asc = d->sense[2];
			d->ascq = d->sense[3];
			d->has_asc = 1;
		}
	}
	return;
}
