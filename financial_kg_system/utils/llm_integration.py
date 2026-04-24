"""
LLM Integration Module
Handles integration with large language models, specifically Alibaba Cloud's Bailian platform
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()

class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text based on the prompt"""
        pass
    
    @abstractmethod
    def embeddings(self, text: str, **kwargs) -> List[float]:
        """Generate embeddings for the given text"""
        pass


class BailianLLMClient(LLMClient):
    """
    Client for Alibaba Cloud Bailian platform (using DashScope API)
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen3"):
        """
        Initialize Bailian client
        
        Args:
            api_key: DashScope/Bailian API key
            model: Model name to use (e.g., 'qwen3', 'qwen-max', etc.)
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY must be set in environment or passed as argument")
        
        self.model = model or os.getenv("LLM_MODEL", "qwen3")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        if not self.api_key:
            raise ValueError("DASHSCOPE API key is required for Bailian integration")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Bailian platform
        
        Args:
            prompt: Input prompt text
            **kwargs: Additional parameters for the model
            
        Returns:
            Generated text response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": kwargs  # Allow passing extra parameters
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if "output" in result and "choices" in result["output"]:
                return result["output"]["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Unexpected response format: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Bailian API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Missing expected fields in response: {str(e)}")
    
    def embeddings(self, text: str, **kwargs) -> List[float]:
        """
        Generate embeddings using Bailian embedding API
        
        Args:
            text: Text to embed
            **kwargs: Additional parameters
            
        Returns:
            Embedding vector as a list of floats
        """
        embedding_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "text-embedding-v1",  # Default embedding model for Bailian
            "input": {
                "texts": [text]
            }
        }
        
        try:
            response = requests.post(embedding_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if "output" in result and "embeddings" in result["output"]:
                return result["output"]["embeddings"][0]["embedding"]
            else:
                raise Exception(f"Unexpected embedding response format: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Bailian Embedding API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Missing expected fields in embedding response: {str(e)}")


class SimpleLLMInterface:
    """
    Simple interface to connect financial graph system to LLMs
    """
    def __init__(self):
        # Set up the LLM client based on environment configuration
        llm_provider = os.getenv("LLM_PROVIDER", "").lower()
        llm_enabled = os.getenv("ENABLE_LLM_INTEGRATION", "false").lower() == "true"
        
        self.client = None
        self.enabled = llm_enabled
        
        if self.enabled and llm_provider == "aliyun-bailian":
            api_key = os.getenv("DASHSCOPE_API_KEY")
            model = os.getenv("LLM_MODEL", "qwen3")
            try:
                self.client = BailianLLMClient(api_key=api_key, model=model)
            except ValueError as e:
                print(f"LLM integration disabled due to missing configuration: {e}")
                self.enabled = False
    
    def query_financial_knowledge(self, question: str, context: Optional[Dict] = None) -> str:
        """
        Query the LLM for financial knowledge with context
        
        Args:
            question: Natural language question about the financial model
            context: Optional financial data context
            
        Returns:
            LLM-generated response
        """
        if not self.enabled or not self.client:
            return "LLM integration is disabled. Please configure LLM settings in environment variables."
        
        # Prepare context-aware prompt for financial data
        prompt = self._construct_financial_prompt(question, context)
        
        try:
            response = self.client.generate_text(prompt)
            return response
        except Exception as e:
            return f"LLM query failed: {str(e)}"
    
    def _construct_financial_prompt(self, question: str, context: Optional[Dict]) -> str:
        """Construct a detailed prompt with financial context"""
        base_prompt = f"你是一个专业的财务分析师，正在分析Excel财务模型。用户提出了以下问题：\n\n{question}\n\n"
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            base_prompt += f"相关的财务数据上下文如下：\n{context_str}\n\n"
        
        base_prompt += "请基于提供的财务数据回答问题，并指出数据来源和计算过程（如果适用）。如果你无法确定答案，请说明原因。"
        
        return base_prompt
    
    def extract_insights(self, financial_data: str) -> Dict[str, Any]:
        """
        Extract insights from financial data using LLM
        
        Args:
            financial_data: Financial data string to analyze
            
        Returns:
            Dictionary containing extracted insights
        """
        if not self.enabled or not self.client:
            return {"error": "LLM integration is disabled"}
        
        prompt = f"""
        作为一个专业的财务分析师，请分析以下财务数据，并提取关键洞察：

        {financial_data}

        请按照以下结构返回分析结果：
        1. 关键指标总结
        2. 趋势分析
        3. 风险提示
        4. 改进建议
        """
        
        try:
            response = self.client.generate_text(prompt, temperature=0.3)
            return {
                "insights": response,
                "provider": "Bailian",
                "model": self.client.model
            }
        except Exception as e:
            return {"error": f"Insight extraction failed: {str(e)}"}
    
    def validate_formulas(self, formulas: List[str]) -> Dict[str, Any]:
        """
        Validate Excel formulas using LLM to check for potential errors
        
        Args:
            formulas: List of Excel formulas to validate
            
        Returns:
            Dictionary with validation results
        """
        if not self.enabled or not self.client:
            return {"error": "LLM integration is disabled"}
        
        formulas_str = "\n".join(formulas)
        prompt = f"""
        请审核以下Excel公式是否有潜在错误或可以改进的地方：

        {formulas_str}

        请为每个公式标注：是否正确、潜在风险、及改进建议。
        """
        
        try:
            response = self.client.generate_text(prompt)
            return {
                "validation_results": response,
                "formulas_checked": len(formulas),
                "provider": "Bailian"
            }
        except Exception as e:
            return {"error": f"Formula validation failed: {str(e)}"}


# For testing and initialization
def get_llm_interface() -> SimpleLLMInterface:
    """
    Get singleton instance of LLM interface
    """
    load_dotenv()
    return SimpleLLMInterface()


# Example usage:
if __name__ == "__main__":
    # Test the client setup
    try:
        llm_interface = get_llm_interface()
        print("LLM Interface created successfully.")
        print(f"Enabled: {llm_interface.enabled}")
        if llm_interface.client:
            print(f"Provider: {type(llm_interface.client).__name__}")
    except Exception as e:
        print(f"Error initializing LLM interface: {e}")