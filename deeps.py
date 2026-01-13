# interactive_chat.py
import os
from openai import OpenAI
from dotenv import load_dotenv
import threading

class DeepSeekChat:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.history = []
        self.streaming = False
    
    def chat_stream(self, user_input):
        """流式对话"""
        self.history.append({"role": "user", "content": user_input})
        
        messages = self.history.copy()
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000
            )
            
            full_response = ""
            print("\n🤖 DeepSeek: ", end="", flush=True)
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            print("\n")
            self.history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
    
    def chat_once(self, user_input):
        """一次性对话"""
        self.history.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.history,
                stream=False,
                temperature=0.7,
                max_tokens=2000
            )
            
            reply = response.choices[0].message.content
            print(f"\n🤖 DeepSeek: {reply}\n")
            self.history.append({"role": "assistant", "content": reply})
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
    
    def clear_history(self):
        """清空对话历史"""
        self.history = []
        print("✅ 对话历史已清空")
    
    def show_history(self):
        """显示对话历史"""
        print("\n" + "="*50)
        print("📜 对话历史:")
        print("="*50)
        for i, msg in enumerate(self.history):
            role = "👤 用户" if msg["role"] == "user" else "🤖 AI"
            print(f"{i+1}. {role}: {msg['content'][:100]}...")
        print("="*50)

def main():
    chat = DeepSeekChat()
    
    print("🚀 DeepSeek 交互式对话开始")
    print("输入 '退出' 或 'exit' 结束对话")
    print("输入 '清空' 或 'clear' 清空历史")
    print("输入 '历史' 或 'history' 查看历史")
    print("输入 '流式' 或 'stream' 切换流式输出")
    print("="*50)
    
    use_stream = False
    
    while True:
        user_input = input("\n👤 你: ").strip()
        
        if user_input.lower() in ['退出', 'exit', 'quit']:
            print("👋 再见！")
            break
        elif user_input.lower() in ['清空', 'clear']:
            chat.clear_history()
            continue
        elif user_input.lower() in ['历史', 'history']:
            chat.show_history()
            continue
        elif user_input.lower() in ['流式', 'stream']:
            use_stream = not use_stream
            mode = "流式" if use_stream else "非流式"
            print(f"✅ 已切换到{mode}模式")
            continue
        elif not user_input:
            continue
        
        if use_stream:
            chat.chat_stream(user_input)
        else:
            chat.chat_once(user_input)

if __name__ == "__main__":
    main()