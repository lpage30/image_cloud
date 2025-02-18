# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

cdef enum LoggerLevel:
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOT_SET = 0

cdef struct BaseLogger:
    LoggerLevel level

cdef void set_logger(int level, object callback) noexcept nogil
cdef void log_error(const char* format, ...) noexcept nogil
cdef void log_warning(const char* format, ...) noexcept nogil
cdef void log_info(const char* format, ...) noexcept nogil
cdef void log_debug(const char* format, ...) noexcept nogil

cdef void log_py(LoggerLevel level, str msg)