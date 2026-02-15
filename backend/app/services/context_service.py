import logging
from typing import List, Any
import tiktoken
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

logger = logging.getLogger("app.context_service")

class ContextService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = 4000  # Threshold for compression

    def _get_token_count(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def _messages_to_text(self, messages: List[BaseMessage]) -> str:
        text = ""
        for m in messages:
            role = "User" if isinstance(m, HumanMessage) else "Assistant" if isinstance(m, AIMessage) else "System"
            text += f"{role}: {m.content}\n"
        return text

    async def compress_context(
        self, 
        chat_history: List[BaseMessage], 
        new_message: str,
        max_context_tokens: int = 2000
    ) -> List[BaseMessage]:
        """
        Compress chat history using FAISS if it exceeds max_tokens.
        Returns a list of messages: [SystemMessage, RelevantContextMessage, LastFewMessages]
        """
        system_msg = None
        other_msgs = []
        for m in chat_history:
            if isinstance(m, SystemMessage):
                system_msg = m
            else:
                other_msgs.append(m)

        total_text = self._messages_to_text(other_msgs)
        if self._get_token_count(total_text) < self.max_tokens:
            return chat_history

        logger.info("Chat history exceeds token limit, compressing with FAISS...")

        # Create documents from messages
        docs = []
        for i, m in enumerate(other_msgs):
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            docs.append(Document(
                page_content=f"{role}: {m.content}",
                metadata={"index": i, "role": role}
            ))

        # Build FAISS index
        vectorstore = await FAISS.afrom_documents(docs, self.embeddings)
        
        # Retrieve relevant messages for the new input
        relevant_docs = await vectorstore.asimilarity_search(new_message, k=5)
        
        # Sort by original index to maintain order
        relevant_docs.sort(key=lambda x: x.metadata["index"])
        
        context_text = "--- RELEVANT PAST CONTEXT ---\n"
        for d in relevant_docs:
            context_text += d.page_content + "\n"
        context_text += "--- END OF CONTEXT ---\n"

        compressed_history = []
        if system_msg:
            compressed_history.append(system_msg)
        
        compressed_history.append(SystemMessage(content=f"The following is relevant context from your previous conversation:\n\n{context_text}"))
        
        # Always include the last 2 messages for immediate continuity
        last_few = other_msgs[-2:] if len(other_msgs) >= 2 else other_msgs
        compressed_history.extend(last_few)

        return compressed_history
