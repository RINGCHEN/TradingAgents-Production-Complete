#!/usr/bin/env python3
"""
投資人格測試服務
處理投資人格測試的邏輯和結果計算
"""
import logging
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PersonalityType(Enum):
    COLD_HUNTER = "cold_hunter"
    WISE_ELDER = "wise_elder"
    SENSITIVE_RADAR = "sensitive_radar"
    BRAVE_WARRIOR = "brave_warrior"
    CAUTIOUS_GUARDIAN = "cautious_guardian"
    EMOTIONAL_ROLLER = "emotional_roller"

@dataclass
class DimensionScores:
    risk_tolerance: float = 50.0
    emotional_control: float = 50.0
    analytical_thinking: float = 50.0
    market_sensitivity: float = 50.0
    long_term_vision: float = 50.0

    def normalize(self) -> 'DimensionScores':
        """標準化到0-100範圍"""
        return DimensionScores(
            risk_tolerance=max(0, min(100, self.risk_tolerance + 50)),
            emotional_control=max(0, min(100, self.emotional_control + 50)),
            analytical_thinking=max(0, min(100, self.analytical_thinking + 50)),
            market_sensitivity=max(0, min(100, self.market_sensitivity + 50)),
            long_term_vision=max(0, min(100, self.long_term_vision + 50))
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "risk_tolerance": self.risk_tolerance,
            "emotional_control": self.emotional_control,
            "analytical_thinking": self.analytical_thinking,
            "market_sensitivity": self.market_sensitivity,
            "long_term_vision": self.long_term_vision
        }

@dataclass
class TestQuestion:
    id: str
    scenario: str
    question: str
    options: List[Dict[str, Any]]

@dataclass
class TestAnswer:
    question_id: str
    selected_option: int
    weights: Dict[str, float]

@dataclass
class PersonalityResult:
    personality_type: PersonalityType
    dimension_scores: DimensionScores
    percentile: float
    description: str
    recommendations: List[str]
    share_content: Dict[str, Any]
    session_id: str
    completed_at: datetime

class PersonalityTestService:
    """投資人格測試服務"""
    
    def __init__(self, db_path: str = "tradingagents.db"):
        self.db_path = db_path
        self.questions = self._load_questions()
        self.personality_types = self._load_personality_types()

    def get_connection(self):
        """獲取數據庫連接"""
        return sqlite3.connect(self.db_path)

    def _load_questions(self) -> List[TestQuestion]:
        """載入測試問題"""
        questions = [
            TestQuestion(
                id="q1",
                scenario="2025年某日，AI技術突破導致科技股暴跌30%，你持有的科技股組合一夜間蒸發50萬台幣。",
                question="隔天開盤前，你會如何反應？",
                options=[
                    {
                        "text": "立即全部賣出，保住剩餘資金",
                        "weights": {"risk_tolerance": -20, "emotional_control": -15}
                    },
                    {
                        "text": "加碼買入，相信這是千載難逢的機會",
                        "weights": {"risk_tolerance": 25, "analytical_thinking": 20}
                    },
                    {
                        "text": "維持持有，等待市場回穩",
                        "weights": {"emotional_control": 15, "long_term_vision": 20}
                    },
                    {
                        "text": "賣出一半，降低風險敞口",
                        "weights": {"risk_tolerance": 5, "analytical_thinking": 10}
                    }
                ]
            ),
            TestQuestion(
                id="q2",
                scenario="你的朋友在群組炫耀，靠某支\"神秘股票\"一週賺了200%，現在股價還在飆漲，媒體瘋狂報導。",
                question="你會如何處理這個\"機會\"？",
                options=[
                    {
                        "text": "立刻跟進買入，不想錯過",
                        "weights": {"market_sensitivity": -20, "emotional_control": -25}
                    },
                    {
                        "text": "深入研究公司基本面再決定",
                        "weights": {"analytical_thinking": 25, "long_term_vision": 15}
                    },
                    {
                        "text": "小額試水，控制風險",
                        "weights": {"risk_tolerance": 10, "emotional_control": 10}
                    },
                    {
                        "text": "完全忽略，堅持自己的策略",
                        "weights": {"emotional_control": 20, "long_term_vision": 25}
                    }
                ]
            ),
            TestQuestion(
                id="q3",
                scenario="一位\"可靠消息人士\"告訴你，某家公司下週將宣布重大併購案，股價可能暴漲50%。",
                question="面對這個\"內線消息\"，你的反應是？",
                options=[
                    {
                        "text": "重倉買入，機不可失",
                        "weights": {"risk_tolerance": 15, "analytical_thinking": -30}
                    },
                    {
                        "text": "小額投資，萬一是真的呢",
                        "weights": {"risk_tolerance": 5, "emotional_control": -10}
                    },
                    {
                        "text": "完全不信，繼續原計劃",
                        "weights": {"analytical_thinking": 25, "emotional_control": 20}
                    },
                    {
                        "text": "反向思考，可能是陷阱",
                        "weights": {"analytical_thinking": 30, "market_sensitivity": 20}
                    }
                ]
            ),
            TestQuestion(
                id="q4",
                scenario="市場已經連續下跌8個月，你的投資組合虧損35%，專家預測還會再跌20%。",
                question="在這種絕望的氛圍中，你會？",
                options=[
                    {
                        "text": "認賠殺出，保住剩餘資金",
                        "weights": {"risk_tolerance": -15, "emotional_control": -20}
                    },
                    {
                        "text": "繼續定期定額投資",
                        "weights": {"long_term_vision": 25, "emotional_control": 20}
                    },
                    {
                        "text": "暫停投資，等待轉機",
                        "weights": {"risk_tolerance": 5, "market_sensitivity": 10}
                    },
                    {
                        "text": "大幅加碼，相信價值投資",
                        "weights": {"risk_tolerance": 30, "long_term_vision": 30}
                    }
                ]
            ),
            TestQuestion(
                id="q5",
                scenario="你更傾向於相信哪種投資建議？",
                question="選擇你最信任的投資依據：",
                options=[
                    {
                        "text": "技術分析圖表和指標",
                        "weights": {"analytical_thinking": 15, "market_sensitivity": 20}
                    },
                    {
                        "text": "公司財報和基本面數據",
                        "weights": {"analytical_thinking": 25, "long_term_vision": 20}
                    },
                    {
                        "text": "知名投資大師的觀點",
                        "weights": {"emotional_control": 10, "long_term_vision": 15}
                    },
                    {
                        "text": "自己的直覺和感覺",
                        "weights": {"market_sensitivity": 10, "emotional_control": -10}
                    }
                ]
            ),
            TestQuestion(
                id="q6",
                scenario="如果你的投資策略連續失敗3次，你會？",
                question="面對連續失敗，你的反應是：",
                options=[
                    {
                        "text": "立即改變策略",
                        "weights": {"market_sensitivity": 15, "emotional_control": -10}
                    },
                    {
                        "text": "檢討並微調策略",
                        "weights": {"analytical_thinking": 20, "emotional_control": 15}
                    },
                    {
                        "text": "堅持原策略，相信長期有效",
                        "weights": {"long_term_vision": 25, "emotional_control": 20}
                    },
                    {
                        "text": "暫停投資，重新學習",
                        "weights": {"analytical_thinking": 15, "risk_tolerance": -5}
                    }
                ]
            ),
            TestQuestion(
                id="q7",
                scenario="你願意承受多大的年度虧損來追求更高回報？",
                question="選擇你的風險承受度：",
                options=[
                    {
                        "text": "0-5%，安全第一",
                        "weights": {"risk_tolerance": -20, "long_term_vision": 10}
                    },
                    {
                        "text": "5-15%，穩健成長",
                        "weights": {"risk_tolerance": 5, "emotional_control": 15}
                    },
                    {
                        "text": "15-30%，積極投資",
                        "weights": {"risk_tolerance": 20, "market_sensitivity": 15}
                    },
                    {
                        "text": "30%以上，高風險高回報",
                        "weights": {"risk_tolerance": 35, "emotional_control": 10}
                    }
                ]
            ),
            TestQuestion(
                id="q8",
                scenario="面對市場波動，你的睡眠品質如何？",
                question="市場波動對你的影響程度：",
                options=[
                    {
                        "text": "完全不受影響，照常睡覺",
                        "weights": {"emotional_control": 25, "long_term_vision": 20}
                    },
                    {
                        "text": "偶爾會想到，但不影響睡眠",
                        "weights": {"emotional_control": 15, "risk_tolerance": 10}
                    },
                    {
                        "text": "經常失眠，擔心投資",
                        "weights": {"emotional_control": -15, "risk_tolerance": -10}
                    },
                    {
                        "text": "半夜會起來看盤",
                        "weights": {"emotional_control": -25, "market_sensitivity": 15}
                    }
                ]
            )
        ]
        return questions

    def _load_personality_types(self) -> Dict[PersonalityType, Dict[str, Any]]:
        """載入人格類型定義"""
        return {
            PersonalityType.COLD_HUNTER: {
                "title": "冷血獵手",
                "description": "你是市場中的頂級掠食者，在別人恐慌時貪婪，在別人貪婪時恐慌。危機就是你的機會。",
                "celebrity_comparison": "你的投資風格類似華倫·巴菲特的冷靜和索羅斯的敏銳",
                "share_text": "我是冷血獵手！在市場血流成河時，我看到的是機會 🦅 #投資人格測試",
                "characteristics": ["高風險承受度", "優秀情緒控制", "理性分析能力"],
                "investment_style": "逆向投資，危機入市"
            },
            PersonalityType.WISE_ELDER: {
                "title": "智慧長者",
                "description": "你是價值投資的信徒，相信時間的力量。短期波動無法動搖你的信念。",
                "celebrity_comparison": "你的投資哲學接近查理·蒙格的智慧和耐心",
                "share_text": "我是智慧長者！時間是我最好的朋友 ⏰ #價值投資 #投資人格測試",
                "characteristics": ["長期視野", "理性分析", "穩健風險控制"],
                "investment_style": "價值投資，長期持有"
            },
            PersonalityType.SENSITIVE_RADAR: {
                "title": "敏感雷達",
                "description": "你對市場變化極其敏感，能捕捉到微妙的信號。但有時過度反應。",
                "celebrity_comparison": "你的市場嗅覺類似彼得·林奇的敏銳",
                "share_text": "我是敏感雷達！市場的一舉一動都逃不過我的眼睛 📡 #投資人格測試",
                "characteristics": ["高市場敏感度", "快速反應能力", "趨勢捕捉"],
                "investment_style": "趨勢跟隨，靈活調整"
            },
            PersonalityType.BRAVE_WARRIOR: {
                "title": "勇敢戰士",
                "description": "你勇於承擔風險，相信直覺。有時會因為過度自信而受傷。",
                "celebrity_comparison": "你的投資風格類似卡爾·伊坎的激進",
                "share_text": "我是勇敢戰士！高風險高回報，富貴險中求 ⚔️ #投資人格測試",
                "characteristics": ["高風險承受度", "直覺決策", "積極進取"],
                "investment_style": "成長投資，積極進取"
            },
            PersonalityType.CAUTIOUS_GUARDIAN: {
                "title": "謹慎守護者",
                "description": "你是資產的守護者，寧可錯過機會也不願承擔風險。穩健是你的座右銘。",
                "celebrity_comparison": "你的投資理念類似約翰·博格的指數投資",
                "share_text": "我是謹慎守護者！穩健投資，細水長流 🛡️ #投資人格測試",
                "characteristics": ["低風險偏好", "穩健策略", "長期規劃"],
                "investment_style": "保守投資，分散風險"
            },
            PersonalityType.EMOTIONAL_ROLLER: {
                "title": "情緒過山車",
                "description": "你的投資情緒隨市場起伏，容易被短期波動影響決策。需要學會控制情緒。",
                "celebrity_comparison": "你需要學習巴菲特的情緒控制",
                "share_text": "我是情緒過山車！投資路上跌宕起伏，但我在學習成長 🎢 #投資人格測試",
                "characteristics": ["情緒波動大", "易受影響", "需要指導"],
                "investment_style": "需要系統化投資紀律"
            }
        }

    async def start_test_session(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """開始測試會話"""
        try:
            session_id = str(uuid.uuid4())
            
            # 創建測試會話記錄
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 創建測試會話表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personality_test_sessions (
                    id TEXT PRIMARY KEY,
                    user_info TEXT,
                    current_question INTEGER DEFAULT 0,
                    answers TEXT DEFAULT '[]',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT
                )
            """)
            
            cursor.execute("""
                INSERT INTO personality_test_sessions (id, user_info)
                VALUES (?, ?)
            """, (session_id, json.dumps(user_info)))
            
            conn.commit()
            conn.close()
            
            return {
                "session_id": session_id,
                "total_questions": len(self.questions),
                "current_question": 0,
                "question": self._format_question(self.questions[0])
            }
            
        except Exception as e:
            logger.error(f"開始測試會話失敗: {e}")
            return {"error": "測試會話創建失敗"}

    async def submit_answer(self, session_id: str, question_id: str, selected_option: int) -> Dict[str, Any]:
        """提交答案並獲取下一題"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 獲取會話信息
            cursor.execute("""
                SELECT current_question, answers FROM personality_test_sessions 
                WHERE id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return {"error": "測試會話不存在"}
            
            current_question, answers_json = row
            answers = json.loads(answers_json) if answers_json else []
            
            # 添加答案
            question = next((q for q in self.questions if q.id == question_id), None)
            if not question:
                return {"error": "問題不存在"}
            
            if selected_option >= len(question.options):
                return {"error": "選項無效"}
            
            answer = TestAnswer(
                question_id=question_id,
                selected_option=selected_option,
                weights=question.options[selected_option]["weights"]
            )
            
            answers.append({
                "question_id": answer.question_id,
                "selected_option": answer.selected_option,
                "weights": answer.weights
            })
            
            next_question_index = current_question + 1
            
            # 更新會話
            cursor.execute("""
                UPDATE personality_test_sessions 
                SET current_question = ?, answers = ?
                WHERE id = ?
            """, (next_question_index, json.dumps(answers), session_id))
            
            conn.commit()
            conn.close()
            
            # 檢查是否完成測試
            if next_question_index >= len(self.questions):
                # 計算結果
                result = await self.calculate_result(session_id, answers)
                return {
                    "completed": True,
                    "result": result
                }
            else:
                # 返回下一題
                next_question = self.questions[next_question_index]
                return {
                    "completed": False,
                    "current_question": next_question_index,
                    "total_questions": len(self.questions),
                    "question": self._format_question(next_question),
                    "progress": (next_question_index / len(self.questions)) * 100
                }
                
        except Exception as e:
            logger.error(f"提交答案失敗: {e}")
            return {"error": "答案提交失敗"}

    async def calculate_result(self, session_id: str, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算測試結果"""
        try:
            # 計算維度得分
            scores = DimensionScores()
            
            for answer in answers:
                weights = answer["weights"]
                scores.risk_tolerance += weights.get("risk_tolerance", 0)
                scores.emotional_control += weights.get("emotional_control", 0)
                scores.analytical_thinking += weights.get("analytical_thinking", 0)
                scores.market_sensitivity += weights.get("market_sensitivity", 0)
                scores.long_term_vision += weights.get("long_term_vision", 0)
            
            # 標準化得分
            normalized_scores = scores.normalize()
            
            # 確定人格類型
            personality_type = self._determine_personality_type(normalized_scores)
            
            # 計算擊敗百分比（模擬）
            percentile = self._calculate_percentile(normalized_scores)
            
            # 獲取人格類型信息
            type_info = self.personality_types[personality_type]
            
            # 生成個性化建議
            recommendations = self._generate_recommendations(personality_type, normalized_scores)
            
            # 創建結果
            result = PersonalityResult(
                personality_type=personality_type,
                dimension_scores=normalized_scores,
                percentile=percentile,
                description=type_info["description"],
                recommendations=recommendations,
                share_content={
                    "title": type_info["title"],
                    "share_text": type_info["share_text"],
                    "celebrity_comparison": type_info["celebrity_comparison"],
                    "percentile": percentile
                },
                session_id=session_id,
                completed_at=datetime.now()
            )
            
            # 保存結果到數據庫
            await self._save_result(session_id, result)
            
            return {
                "personality_type": {
                    "type": personality_type.value,
                    "title": type_info["title"],
                    "description": type_info["description"],
                    "celebrity_comparison": type_info["celebrity_comparison"],
                    "characteristics": type_info["characteristics"],
                    "investment_style": type_info["investment_style"]
                },
                "dimension_scores": normalized_scores.to_dict(),
                "percentile": percentile,
                "recommendations": recommendations,
                "share_content": result.share_content,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"計算測試結果失敗: {e}")
            return {"error": "結果計算失敗"}

    def _format_question(self, question: TestQuestion) -> Dict[str, Any]:
        """格式化問題"""
        return {
            "id": question.id,
            "scenario": question.scenario,
            "question": question.question,
            "options": [{"text": opt["text"], "index": i} for i, opt in enumerate(question.options)]
        }

    def _determine_personality_type(self, scores: DimensionScores) -> PersonalityType:
        """確定人格類型"""
        # 基於得分組合確定人格類型
        if (scores.risk_tolerance >= 70 and scores.emotional_control >= 70 and 
            scores.analytical_thinking >= 70):
            return PersonalityType.COLD_HUNTER
        elif (scores.long_term_vision >= 70 and scores.analytical_thinking >= 70 and
              scores.risk_tolerance >= 50):
            return PersonalityType.WISE_ELDER
        elif (scores.market_sensitivity >= 70 and scores.analytical_thinking >= 60):
            return PersonalityType.SENSITIVE_RADAR
        elif (scores.risk_tolerance >= 70 and scores.emotional_control >= 50):
            return PersonalityType.BRAVE_WARRIOR
        elif (scores.risk_tolerance <= 40 and scores.emotional_control >= 60 and
              scores.long_term_vision >= 60):
            return PersonalityType.CAUTIOUS_GUARDIAN
        else:
            return PersonalityType.EMOTIONAL_ROLLER

    def _calculate_percentile(self, scores: DimensionScores) -> float:
        """計算擊敗百分比（模擬）"""
        # 基於總分計算百分比
        total_score = (scores.risk_tolerance + scores.emotional_control + 
                      scores.analytical_thinking + scores.market_sensitivity + 
                      scores.long_term_vision) / 5
        
        # 模擬正態分佈
        if total_score >= 80:
            return 90 + (total_score - 80) / 2
        elif total_score >= 60:
            return 70 + (total_score - 60)
        elif total_score >= 40:
            return 30 + (total_score - 40) * 2
        else:
            return total_score * 0.75

    def _generate_recommendations(self, personality_type: PersonalityType, 
                                scores: DimensionScores) -> List[str]:
        """生成個性化建議"""
        recommendations = []
        
        if personality_type == PersonalityType.COLD_HUNTER:
            recommendations = [
                "繼續保持冷靜的投資心態，這是你的最大優勢",
                "可以考慮更多逆向投資機會",
                "適合進行價值投資和危機入市策略"
            ]
        elif personality_type == PersonalityType.WISE_ELDER:
            recommendations = [
                "堅持長期價值投資策略",
                "定期檢視投資組合，但避免頻繁交易",
                "可以考慮指數基金和藍籌股投資"
            ]
        elif personality_type == PersonalityType.SENSITIVE_RADAR:
            recommendations = [
                "善用你的市場敏感度，但要控制交易頻率",
                "建立明確的停損和停利點",
                "適合技術分析和趨勢跟隨策略"
            ]
        elif personality_type == PersonalityType.BRAVE_WARRIOR:
            recommendations = [
                "控制單筆投資的風險敞口",
                "建立更嚴格的風險管理制度",
                "適合成長股和新興市場投資"
            ]
        elif personality_type == PersonalityType.CAUTIOUS_GUARDIAN:
            recommendations = [
                "保持穩健的投資風格",
                "可以適度增加一些成長性投資",
                "建議定期定額投資和資產配置"
            ]
        else:  # EMOTIONAL_ROLLER
            recommendations = [
                "建立系統化的投資紀律",
                "避免在情緒激動時做投資決策",
                "考慮尋求專業投資顧問的協助"
            ]
        
        return recommendations

    async def _save_result(self, session_id: str, result: PersonalityResult):
        """保存測試結果"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            result_data = {
                "personality_type": result.personality_type.value,
                "dimension_scores": result.dimension_scores.to_dict(),
                "percentile": result.percentile,
                "description": result.description,
                "recommendations": result.recommendations,
                "share_content": result.share_content
            }
            
            cursor.execute("""
                UPDATE personality_test_sessions 
                SET completed_at = ?, result = ?
                WHERE id = ?
            """, (result.completed_at.isoformat(), json.dumps(result_data), session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存測試結果失敗: {e}")

    async def get_test_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取測試結果"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT result, completed_at FROM personality_test_sessions 
                WHERE id = ? AND result IS NOT NULL
            """, (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                result_data = json.loads(row[0])
                result_data["completed_at"] = row[1]
                return result_data
            return None
            
        except Exception as e:
            logger.error(f"獲取測試結果失敗: {e}")
            return None