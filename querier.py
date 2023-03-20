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
        self.prompts_sent = []

    def send_query(
            self,
            prompt: BasePromptTemplate,
            initial: str = "",
            **kwargs,
    ):

        query_sent_text = prompt.format_prompt(**kwargs).dict()["text"]
        query_save_object = {"prompt": query_sent_text}

        chain = LLMChain(llm=self.llm, prompt=prompt)

        results = initial + chain.run(**kwargs)
        query_save_object["response"] = results

        token_usage = (len(results) + len(query_sent_text)) / 4
        query_save_object["token_usage"] = token_usage
        self.prompts_sent.append(query_save_object)

        return results

    def calculate_function_tokens(self, function_text: str, functions_used: int):
        tokens_json_response_template = 80
        avg_function_doc_length = 340

        function_tokens = len(function_text) / 4
        function_tokens += tokens_json_response_template
        # base function's template
        if functions_used == 0:
            base_template_tokens = 220
            function_tokens += base_template_tokens
        else:
            composed_template_tokens = 365
            function_tokens += composed_template_tokens
            function_tokens += functions_used * avg_function_doc_length

        return function_tokens


