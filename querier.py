import os
#import promptlayer
from langchain import (
    BasePromptTemplate,
    LLMChain,
)
from langchain.chat_models import ChatOpenAI

#from promptlayer.langchain.llms import OpenAI as PromptLayerOpenAI
from templates import doc_base_function_template


class Querier:
    def __init__(self, openai_api_key: str, promptlayer_api_key: str | None = None):
        # promptlayer.api_key = promptlayer_api_key
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(
            temperature=0.0,
            openai_api_key=self.openai_api_key,
        )

    def send_query(
            self,
            prompt: BasePromptTemplate,
            initial: str = "",
            **kwargs,
    ):
        chain = LLMChain(llm=self.llm, prompt=prompt)
        results = initial + chain.run(**kwargs)
        return results

