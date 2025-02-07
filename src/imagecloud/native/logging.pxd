# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

cdef enum LoggerLevel:
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOT_SET = 0

cdef void set_logger_level(LoggerLevel level) noexcept nogil

cdef int can_log(LoggerLevel level) noexcept nogil

ctypedef int (*log_f)(const char* format, ...) noexcept nogil

cdef log_f log_error() noexcept nogil

cdef log_f log_warning() noexcept nogil

cdef log_f log_info() noexcept nogil

cdef log_f log_debug() noexcept nogil

