#pragma once

#include <chrono>
#include <functional>
#include <mutex>
#include <ostream>
#include <string>
#include <string_view>
#include <vector>

namespace gtavi {

enum class LogLevel {
    Trace = 0,
    Debug,
    Info,
    Warn,
    Error,
    Critical,
};

/// Lowercase name used in log output ("info", "warn", ...).
std::string_view to_string(LogLevel level) noexcept;

/// Streams the same name that to_string() returns.
inline std::ostream& operator<<(std::ostream& stream, LogLevel level) {
    return stream << to_string(level);
}

/// Parses "trace", "debug", "info", "warn"/"warning", "error", "critical".
/// Returns `fallback` when the input is not recognised.
LogLevel log_level_from_string(std::string_view text, LogLevel fallback) noexcept;

struct LogRecord {
    std::chrono::system_clock::time_point time;
    LogLevel level;
    std::string_view message;
};

/// A log destination.
///
/// Sinks are invoked while no internal lock is held, so a sink may itself log
/// to a different Logger. A sink must not log to the Logger that owns it or the
/// recursion will not terminate.
using LogSink = std::function<void(const LogRecord&)>;

/// Thread-safe logger with pluggable sinks.
///
/// The logger owns no output by default. Attach a sink (for example
/// make_stderr_sink()) to make records observable.
class Logger {
  public:
    Logger() = default;

    void set_level(LogLevel level);
    LogLevel level() const;

    bool should_log(LogLevel level) const;

    /// Appends a sink. Sinks run in registration order.
    void add_sink(LogSink sink);
    void clear_sinks();

    void log(LogLevel level, std::string_view message);

    void trace(std::string_view message) { log(LogLevel::Trace, message); }
    void debug(std::string_view message) { log(LogLevel::Debug, message); }
    void info(std::string_view message) { log(LogLevel::Info, message); }
    void warn(std::string_view message) { log(LogLevel::Warn, message); }
    void error(std::string_view message) { log(LogLevel::Error, message); }
    void critical(std::string_view message) { log(LogLevel::Critical, message); }

    /// Process-wide logger used by code that is not given a logger explicitly.
    static Logger& default_logger();

  private:
    mutable std::mutex mutex_;
    LogLevel level_ = LogLevel::Info;
    std::vector<LogSink> sinks_;
};

/// Formats a timestamp as "2026-01-31T12:34:56Z" in UTC.
std::string format_timestamp_iso8601(std::chrono::system_clock::time_point time);

/// Sink that writes "[timestamp] [level] message" lines to stderr.
LogSink make_stderr_sink();

/// Sink that writes to `stream`. The stream must outlive the sink.
LogSink make_stream_sink(std::ostream& stream);

}  // namespace gtavi
