import re

class ParsedQuestion:
    def __init__(self, index, content=""):
        self.index = index
        self.content = content
        self.options = {}
        self.answer = None
        self.explanation = None

class DocumentParser:
    def __init__(self):
        # 选项匹配模式
        self.option_pattern = re.compile(r'^[\(（]?[A-Z][\)）]?[.、．:\s](.+)$')
        
        # 答案匹配模式
        self.answer_pattern = re.compile(
            r'(?:[\[【\(（]?(?:参考)?(?:正确)?(?:标准)?答案[\]】\)）]?|Answer)[:：\s]*(.+)',
            re.IGNORECASE
        )
        
        # 解析匹配模式
        self.explanation_pattern = re.compile(
            r'(?:[\[【\(（]?(?:答案)?(?:解析|分析|说明|详解)[\]】\)）]?|Explanation)[:：\s]*(.+)',
            re.IGNORECASE
        )
        
        # 题目开头模式
        self.question_start_pattern = re.compile(
            r'^(?:[\(（]?\d+[\)）]?[.、．:\s]|第\d+题[\s:：]?|题目\d+[\s:：]?|Question\s*\d+[.:\s])',
            re.IGNORECASE
        )
        
        # 题型标签模式
        self.type_label_pattern = re.compile(
            r'^[一二三四五六七八九十]+[、.．\s]|^[（(]?[一二三四五六七八九十]+[)）]?$|^(?:单选题|多选题|判断题|简答题|填空题|选择题|问答题)[:：\s]*$',
            re.IGNORECASE
        )

    def parse_txt(self, text):
        lines = text.split('\n')
        questions = []
        current_question = None
        question_index = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            print(f"Processing line: {line}")

            if self.type_label_pattern.match(line):
                print("  -> Skipped (Type Label)")
                continue
            
            if self.question_start_pattern.match(line):
                if current_question:
                    questions.append(current_question)
                
                question_index += 1
                # Remove number prefix
                content = re.sub(
                    r'^(?:[\(（]?\d+[\)）]?[.、．:\s]|第\d+题[\s:：]?|题目\d+[\s:：]?|Question\s*\d+[.:\s])', 
                    '', line, flags=re.IGNORECASE
                ).strip()
                
                current_question = ParsedQuestion(question_index, content)
                print(f"  -> New Question: {question_index}. {content}")
                continue

            if current_question:
                # Check option
                opt_match = self.option_pattern.match(line)
                if opt_match:
                    # Need to extract the letter. My regex captures the content, but let's see.
                    # The current regex starts with ^...[A-Z]...
                    # Let's verify the group capture.
                    # Wait, the regex in my previous edit was:
                    # r'^[\(（]?([A-Z])[\)）]?[.、．:\s](.+)$'
                    # So Group 1 is Letter, Group 2 is Content.
                    
                    # Re-compiling for this script to match class logic accurately
                    full_match = re.match(r'^[\(（]?([A-Z])[\)）]?[.、．:\s](.+)$', line)
                    if full_match:
                        key = full_match.group(1)
                        val = full_match.group(2).strip()
                        current_question.options[key] = val
                        print(f"  -> Option {key}: {val}")
                        continue
                
                # Check answer
                ans_match = self.answer_pattern.match(line)
                if ans_match:
                    current_question.answer = ans_match.group(1).strip()
                    print(f"  -> Answer: {current_question.answer}")
                    continue
                
                # Check explanation
                exp_match = self.explanation_pattern.match(line)
                if exp_match:
                    current_question.explanation = exp_match.group(1).strip()
                    print(f"  -> Explanation: {current_question.explanation}")
                    continue
                
                # Append to content
                if not current_question.options:
                    current_question.content += " " + line
                    print(f"  -> Appended to content: {line}")

        if current_question:
            questions.append(current_question)
            
        return questions

# Test data from user
test_data = """
26.从交易性理到方向性战略節理,这是人力资源管理()的转交。
A．组织性质
B．管理职能
C．管理角色
D．管理模式
【参考答案】：D
27.一般而言,竞争策略为()的企业中,员工归属感很高。
A．廉价策略
B．创新策略
C．优质策略
D．投资策略
【参考答案】：C
"""

parser = DocumentParser()
questions = parser.parse_txt(test_data)
print(f"\nTotal questions parsed: {len(questions)}")
for q in questions:
    print(f"Q{q.index}: {q.content}")
    print(f"  Options: {q.options}")
    print(f"  Answer: {q.answer}")
