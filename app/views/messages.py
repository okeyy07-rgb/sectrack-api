"""Terjemahan pesan error bawaan Marshmallow ke Bahasa Indonesia,
supaya semua pesan validasi yang diterima client konsisten satu bahasa.
Modul ini harus di-import SEBELUM schema didefinisikan."""
from marshmallow import Schema, fields, validate

fields.Field.default_error_messages.update(
    {
        "required": "Field ini wajib diisi.",
        "null": "Field ini tidak boleh null.",
        "validator_failed": "Nilai tidak valid.",
    }
)
fields.String.default_error_messages.update({"invalid": "Harus berupa teks."})
fields.Number.default_error_messages.update({"invalid": "Harus berupa angka.", "too_large": "Angka terlalu besar."})
fields.Integer.default_error_messages.update({"invalid": "Harus berupa angka bulat."})
fields.Float.default_error_messages.update({"special": "Nilai NaN/infinity tidak diizinkan."})
fields.Email.default_error_messages.update({"invalid": "Format email tidak valid."})
fields.Boolean.default_error_messages.update({"invalid": "Harus berupa true/false."})
fields.DateTime.default_error_messages.update(
    {"invalid": "Format tanggal-waktu tidak valid, pakai ISO 8601 (contoh: 2026-11-20T09:00:00+07:00)."}
)

validate.Length.message_min = "Minimal {min} karakter."
validate.Length.message_max = "Maksimal {max} karakter."
validate.Length.message_all = "Panjang harus {min} sampai {max} karakter."
validate.OneOf.default_message = "Harus salah satu dari: {choices}."
validate.Range.message_min = "Harus {min_op} {{min}}."
validate.Range.message_max = "Harus {max_op} {{max}}."
validate.Range.message_all = "Harus di antara {{min}} dan {{max}}."
validate.Range.message_gte = "lebih besar atau sama dengan"
validate.Range.message_lte = "lebih kecil atau sama dengan"

Schema._default_error_messages = {
    "type": "Tipe input tidak valid, harus JSON object.",
    "unknown": "Field tidak dikenal.",
}
