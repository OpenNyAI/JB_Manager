## Logger Service:

The logger service operates as a standalone component/service within the Jugalbandi (JB) Manager system. Its primary purpose is to record and manage metrics from other key services: api, language, channel, flow and retriever. These metrics provide valuable insights into the performance of each service, facilitate debugging, and help track user requests and responses as well as the time taken by each service to process them.

### Core Functionality

- **Service Monitoring:** Logs key metrics from each service to enable better analysis and issue identification.
- **Request Tracking:** Tracks user requests and responses across services to ensure seamless flow and response time monitoring.
- **Data Persistence:** Stores service-specific data in respective database tables for future reference and analysis.

### Workflow

When a request or a response passes through a service (api, channel, language, flow, or retriever), a logger object containing service-specific details, is created. These details include relevant identifiers (e.g., User ID, Turn ID, Channel ID) and metadata specific to the service (e.g., Message Type, Intent, Translation Type).
This logger object is sent asynchronously to the logger service via a kafka queue. The logger service receives the logger object from its kafka queue and processes the message by:

1. **Unpacking and identifying the source service:**
    - The message is unpacked upon receipt.
    - The source service from which the message originated is identified.

2. **Logging the details into the respective table:**
    - The corresponding service’s logging function is called in the CRUD layer.
    - This function in the CRUD layer performs the following actions:
        - Creates a database session.
        - Creates an instance of the JB Logger type of the source service with the received data.
        - Adds the object to the relevant logging table in the database.

This flow is repeated for each service, ensuring comprehensive tracking and logging of all relevant metrics across the system.

### Data logged for the each service

1. **API:** Turn id of the request, user id of the user accessing the bot and the session id.

2. **Channel:** Channel id and channel name to identify the channel, message intent indicating if the message is incoming or outgoing, type of message (e.g., text, dialog etc) and the service it is sent to.

3. **Language:** Message state to record the incoming/outgoing/intermediate state of message, message language to record its current language, message type (e.g., text, audio etc), language it is translated to and the translation type (e.g., speech to text, language translation, text to speech etc), along with the model used for translation and the response time required for translation.

4. **Flow:** Session id, message intent indicating if the message is incoming or outgoing, flow intent (e.g., user input, dialog etc.) and the service message is sent to.

5. **Retriever:** Retriever type (r2r or default), collection name, top_chunk_k_value indicating number of chunks being considered to generate response, total number of chunks, a list of each chunk content being considered to generate response and the request query.

Along with this data, turn id and the status of each message indicating whether the message has been processed properly by the service, is recorded.