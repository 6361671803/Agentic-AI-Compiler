from crewai import Agent

debug_agent = Agent(
    role="Python Debugger",
    goal="Find and fix Python errors",
    backstory="Expert AI agent specialized in Python debugging",
    verbose=True
)
