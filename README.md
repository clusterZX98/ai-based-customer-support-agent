# AI Based Customer Support Agent

An AI-powered customer support agent designed to handle customer queries, retrieve relevant information, maintain conversation context, access customer and order data, and escalate complex issues when human intervention is required.

The project combines large language models, agent workflows, knowledge retrieval, tool calling, and persistent memory to create a practical customer support automation system.

## Overview

Traditional customer support systems often depend on predefined rules, static FAQs, and manual ticket handling.

This project aims to build a more intelligent support system that can understand customer queries, determine the appropriate action, retrieve relevant information, and respond using contextual information.

The agent can work with:

- Customer information
- Order information
- Support tickets
- Frequently asked questions
- Shipping policies
- Refund policies
- Payment policies
- Cancellation policies
- Conversation memory
- Long-term customer memory
- Support escalation

The system is designed around an agent workflow where different tools and states are used depending on the customer's request.

## Key Features

### AI Customer Support

The system can understand natural language customer queries and generate appropriate responses.

Examples include:

- "Where is my order?"
- "I want to cancel my order."
- "What is your refund policy?"
- "My payment failed."
- "I received the wrong product."
- "Can I get a refund?"
- "I need help with my previous issue."

### Knowledge Base

The project contains a dedicated knowledge base containing support-related information.

Current knowledge base files include:

- FAQ
- Cancellation Policy
- Payment Policy
- Refund Policy
- Shipping Policy

The agent can search the knowledge base and use the retrieved information when responding to customers.

### Customer Lookup

The customer lookup tool allows the agent to retrieve customer information from the available customer data.

This allows responses to be based on customer-specific information instead of relying only on generic responses.

### Order Lookup

The order lookup tool allows the agent to retrieve order-related information.

For example, the agent can use order information to answer questions related to:

- Order status
- Order details
- Shipping
- Customer orders
- Delivery-related issues

### Ticket Handling

The system contains ticket data and supports customer-support workflows involving support tickets.

This allows the project to move beyond a simple question-answering chatbot toward a more realistic customer service system.

### Escalation

Some customer issues require human intervention.

The escalation component allows the agent to identify situations where the issue should be transferred to a human support representative.

Examples include:

- Complex complaints
- Issues requiring manual investigation
- Problems that cannot be resolved using available information
- Cases requiring human approval

### Conversation Memory

The project includes memory components that allow the system to maintain context across conversations.

The memory architecture contains:

- Short-term conversation state
- Conversation checkpoints
- Long-term memory

This helps the agent maintain continuity instead of treating every customer message as an isolated request.

### Agent Workflow

The project uses a structured agent workflow to determine what should happen after receiving a customer query.

A simplified workflow is:

Customer Query
       |
       v
Understand Request
       |
       v
Determine Required Action
       |
       +----------------------+
       |                      |
       v                      v
Knowledge Search       Customer/Order Lookup
       |                      |
       +----------+-----------+
                  |
                  v
             Generate Response
                  |
                  v
          Need Human Support?
             /          \
           Yes           No
            |             |
            v             v
        Escalation      Response


## Project Architecture

The project is organised into separate components for agents, tools, data, memory, knowledge, and persistent storage.

```text
ai-customer-support-agent/
│
├── agent/
│   ├── __init__.py
│   ├── graph.py
│   ├── nodes.py
│   ├── prompts.py
│   ├── runtime.py
│   └── state.py
│
├── data/
│   ├── customers.json
│   ├── orders.json
│   └── tickets.json
│
├── database/
│   ├── conversation_checkpoints.db
│   ├── conversation_checkpoints.db-shm
│   ├── conversation_checkpoints.db-wal
│   └── long_term_memory.db
│
├── knowledge_base/
│   ├── cancellation_policy.txt
│   ├── faq.txt
│   ├── payment_policy.txt
│   ├── refund_policy.txt
│   └── shipping_policy.txt
│
├── memory/
│   ├── __init__.py
│   ├── manager.py
│   └── runtime.py
│
├── tools/
│   ├── __init__.py
│   ├── customer_lookup.py
│   ├── escalation.py
│   ├── knowledge_search.py
│   └── order_lookup.py
│
├── app.py
├── .env
├── .gitignore
└── README.md
