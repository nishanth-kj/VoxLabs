#pragma once
#include <string>

namespace voxlabs {
namespace utils {

class Logger {
public:
    static void info(const std::string& message);
    static void error(const std::string& message);
};

} // namespace utils
} // namespace voxlabs
