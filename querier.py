import os
import promptlayer
from langchain import (
    BasePromptTemplate,
    LLMChain,
    OpenAI
)
from promptlayer.langchain.llms import OpenAI as PromptLayerOpenAI
from templates import doc_base_function_template


class Querier:
    def __init__(self, openai_api_key: str, promptlayer_api_key: str | None = None):
        promptlayer.api_key = promptlayer_api_key
        self.openai_api_key = openai_api_key
        llm_mode = OpenAI if promptlayer_api_key is None else PromptLayerOpenAI
        print(llm_mode)
        self.llm = llm_mode(
            temperature=0.0,
            openai_api_key=self.openai_api_key,
            pl_tags=["langchain-request"],
        )

    def send_query(
            self,
            prompt: BasePromptTemplate,
            initial: str = "",
            pl_tags=None,
            **kwargs,
    ):
        if pl_tags is None:
            pl_tags = ["documented function"]
        self.llm.pl_tags = pl_tags
        chain = LLMChain(llm=self.llm, prompt=prompt)
        results = initial + chain.run(**kwargs)
        return results

