"""Exception domain yang dipakai layer service/repository.

Dibuat terpisah agar views / htmx bisa menangkap error bisnis
dengan tipe yang jelas (bukan Exception generik).
"""


class DomainError(Exception):
    """Error bisnis yang bisa ditampilkan langsung ke user (bahasa Indonesia)."""


class NotFoundError(DomainError):
    """Data yang dicari tidak ditemukan."""


class DuplicateSalesOrderError(DomainError):
    """Sales Order sudah pernah dititipkan (dicegah duplikasi batch)."""


class InvalidStatusTransitionError(DomainError):
    """Transisi status withdrawal tidak sah (lompat/mundur)."""


class InsufficientStockError(DomainError):
    """Stok titipan tidak mencukupi / akan minus."""


class OtpInvalidError(DomainError):
    """Kode OTP salah / format tidak valid."""


class OtpExpiredError(DomainError):
    """Kode OTP sudah kedaluwarsa (TTL habis)."""


class OtpAlreadyUsedError(DomainError):
    """Kode OTP sudah pernah dipakai (sekali pakai)."""


class SuratJalanAlreadyPrintedError(DomainError):
    """Surat Jalan sudah pernah dicetak (tidak boleh print ulang)."""


class DasaApiError(DomainError):
    """Gagal memanggil / memproses response API DASA."""


class DasaMappingError(DomainError):
    """Struktur response DASA tidak sesuai yang diharapkan (key tidak ditemukan)."""
