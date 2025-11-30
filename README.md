AutomationHub

AutomationHub is a Python-based automation server designed to streamline task management, meeting scheduling, and developer workflow. It integrates with Zoho Cliq for real-time notifications and Jira for task tracking, allowing teams to handle tasks and meetings efficiently from a single interface.

⚡ Key Features

Message Parsing & Categorization
Automatically analyzes messages sent to the server via Zoho Cliq and classifies them into categories such as Developer Issue, Task Creation, or Meeting Creation.

Jira Task Creation
Parsed tasks can be automatically created in Jira, including subject, description, deadline, and urgency. Ensures all developer issues are tracked in a project management system.

Meeting Scheduling
Schedule meetings directly through Google Calendar integration and generate meeting links automatically. Notifications are sent back to Zoho Cliq.

Zoho Cliq Integration
Receive messages from Zoho Cliq and post updates, confirmations, or meeting links to a channel in real-time.

Configurable via Environment Variables
All API keys, tokens, and credentials are stored securely in a .env file.
