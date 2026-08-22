#include "utils/logger.h"
#include <iostream>

namespace voxlabs {
namespace utils {

void Logger::info(const std::string& message) {
	std::cout << "[INFO] " << message << std::endl;
}

void Logger::error(const std::string& message) {
	std::cerr << "[ERROR] " << message << std::endl;
}

} // namespace utils
} // namespace voxlabs
