from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.benchmark_agent import benchmark_handler

# Create app and register handler
app = BedrockAgentCoreApp(debug=True)
app.entrypoint(benchmark_handler)

if __name__ == "__main__":
    app.run()


# Updated Sun Jan 18 22:55:51 CST 2026
