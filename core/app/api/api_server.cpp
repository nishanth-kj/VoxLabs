#include "api_server.h"
#include "utils/logger.h"
#include <drogon/drogon.h>

namespace voxlabs {
namespace app {

ApiServer::ApiServer(services::VoiceService& service, controllers::VoiceController& controller) 
    : voiceService(service), voiceController(controller) {
    utils::Logger::info("API Server instantiated");
}

ApiServer::~ApiServer() {
}

void ApiServer::start(int port) {
    utils::Logger::info("Starting API Server on port " + std::to_string(port));
    
    // Configure Drogon server
    drogon::app().addListener("0.0.0.0", port);
    
    // Add a test route
    drogon::app().registerHandler(
        "/api/health",
        [](const drogon::HttpRequestPtr& req,
           std::function<void (const drogon::HttpResponsePtr &)> &&callback) {
            auto resp = drogon::HttpResponse::newHttpResponse();
            resp->setStatusCode(drogon::k200OK);
            resp->setBody("{\"status\":\"ok\"}");
            callback(resp);
        },
        {drogon::Get}
    );

    // Register VoiceController routes
    drogon::app().registerHandler(
        "/api/clone",
        [this](const drogon::HttpRequestPtr& req,
           std::function<void (const drogon::HttpResponsePtr &)> &&callback) {
            std::string result = voiceController.handleCloneVoiceRequest(std::string(req->getBody()));
            auto resp = drogon::HttpResponse::newHttpResponse();
            resp->setStatusCode(drogon::k200OK);
            resp->setBody(result);
            callback(resp);
        },
        {drogon::Post}
    );

    drogon::app().registerHandler(
        "/api/synthesize",
        [this](const drogon::HttpRequestPtr& req,
           std::function<void (const drogon::HttpResponsePtr &)> &&callback) {
            std::string result = voiceController.handleSynthesizeRequest(std::string(req->getBody()));
            auto resp = drogon::HttpResponse::newHttpResponse();
            resp->setStatusCode(drogon::k200OK);
            resp->setBody(result);
            callback(resp);
        },
        {drogon::Post}
    );

    drogon::app().registerHandler(
        "/api/test",
        [this](const drogon::HttpRequestPtr& req,
           std::function<void (const drogon::HttpResponsePtr &)> &&callback) {
            std::string result = voiceController.handleTestRequest(std::string(req->getBody()));
            auto resp = drogon::HttpResponse::newHttpResponse();
            resp->setStatusCode(drogon::k200OK);
            resp->setBody(result);
            callback(resp);
        },
        {drogon::Get, drogon::Post}
    );

    drogon::app().run();
}

void ApiServer::stop() {
    drogon::app().quit();
}

} // namespace app
} // namespace voxlabs
