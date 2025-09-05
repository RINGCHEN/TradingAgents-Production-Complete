#!/usr/bin/env python3
"""
增強版投資人格測試服務
任務 0.2.1: 創建獨立投資人格測試網站 - 極端市場情境測試
添加更多極端、話題性的市場情境，提升病毒式傳播潛力
"""

import logging
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .personality_test_service import PersonalityTestService, TestQuestion, PersonalityType, DimensionScores

logger = logging.getLogger(__name__)

class EnhancedPersonalityTestService(PersonalityTestService):
    """增強版投資人格測試服務"""
    
    def __init__(self, db_path: str = "tradingagents.db"):
        super().__init__(db_path)
        # 覆蓋原有問題，使用增強版極端情境問題
        self.questions = self._load_enhanced_questions()
        self.viral_elements = self._load_viral_elements()
    
    def _load_enhanced_questions(self) -> List[TestQuestion]:
        """載入增強版極端市場情境測試問題"""
        questions = [
            TestQuestion(
                id="extreme_q1",
                scenario="🚨 2025年黑天鵝事件：AI突然宣布「股市將在24小時內崩盤90%」，全球恐慌性拋售已開始。你的投資組合在1小時內暴跌40%。",
                question="在這個史無前例的危機中，你的第一反應是？",
                options=[
                    {
                        "text": "🔥 立即ALL IN，這是千年一遇的抄底機會！",
                        "weights": {"risk_tolerance": 40, "analytical_thinking": 25, "emotional_control": 30}
                    },
                    {
                        "text": "💀 瘋狂拋售，能跑多少是多少！",
                        "weights": {"risk_tolerance": -30, "emotional_control": -35, "market_sensitivity": -20}
                    },
                    {
                        "text": "🧠 冷靜分析AI預測的可信度，理性決策",
                        "weights": {"analytical_thinking": 35, "emotional_control": 25, "long_term_vision": 20}
                    },
                    {
                        "text": "🛡️ 部分止損，保留現金等待更多信息",
                        "weights": {"risk_tolerance": 10, "analytical_thinking": 15, "emotional_control": 20}
                    }
                ]
            ),
            TestQuestion(
                id="extreme_q2",
                scenario="💰 你的鄰居大媽靠「狗狗幣」3個月賺了1000萬，現在每天開法拉利上菜市場。她神秘地告訴你下一個「百倍幣」的名字。",
                question="面對這個「財富密碼」，你會？",
                options=[
                    {
                        "text": "🚀 梭哈！大媽都能賺1000萬，我為什麼不行？",
                        "weights": {"market_sensitivity": -25, "emotional_control": -30, "risk_tolerance": 25}
                    },
                    {
                        "text": "🔍 深度研究這個幣的技術和團隊背景",
                        "weights": {"analytical_thinking": 30, "long_term_vision": 20, "emotional_control": 15}
                    },
                    {
                        "text": "💸 投入零花錢試試水，萬一是真的呢？",
                        "weights": {"risk_tolerance": 15, "market_sensitivity": 10, "emotional_control": 5}
                    },
                    {
                        "text": "🙄 完全無視，這種暴富故事我聽太多了",
                        "weights": {"emotional_control": 25, "analytical_thinking": 20, "long_term_vision": 30}
                    }
                ]
            ),
            TestQuestion(
                id="extreme_q3",
                scenario="🎰 你發現了一個「必勝」交易策略：每次虧損就加倍下注，理論上永遠不會虧錢。你已經連續虧損5次，下一筆需要投入你全部身家的80%。",
                question="在這個「賭徒謬誤」的陷阱中，你會？",
                options=[
                    {
                        "text": "💎 堅持到底！數學不會騙人，下一把必勝！",
                        "weights": {"risk_tolerance": 35, "analytical_thinking": -25, "emotional_control": -20}
                    },
                    {
                        "text": "🛑 立即停止，承認策略有問題",
                        "weights": {"analytical_thinking": 30, "emotional_control": 25, "long_term_vision": 20}
                    },
                    {
                        "text": "📊 重新檢視策略，尋找漏洞",
                        "weights": {"analytical_thinking": 35, "emotional_control": 15, "long_term_vision": 15}
                    },
                    {
                        "text": "💰 降低賭注，但繼續執行策略",
                        "weights": {"risk_tolerance": 10, "analytical_thinking": 5, "emotional_control": 10}
                    }
                ]
            ),
            TestQuestion(
                id="extreme_q4",
                scenario="🌊 全球經濟海嘯來襲：通膨飆到30%，銀行倒閉潮，現金變廢紙。你的朋友們有的買黃金、有的囤比特幣、有的搶購房地產。",
                question="在這個「末日場景」中，你的避險策略是？",
                options=[
                    {
                        "text": "🏠 All in 房地產，至少有實體資產",
                        "weights": {"risk_tolerance": 20, "long_term_vision": 25, "analytical_thinking": 15}
                    },
                    {
                        "text": "₿ 全部換成比特幣，數位黃金才是未來",
                        "weights": {"risk_tolerance": 30, "market_sensitivity": 20, "analytical_thinking": 10}
                    },
                    {
                        "text": "🥇 傳統黃金最安全，幾千年都沒變",
                        "weights": {"risk_tolerance": 5, "long_term_vision": 30, "emotional_control": 20}
                    },
                    {
                        "text": "🎯 分散投資各種資產，不把雞蛋放同一籃子",
                        "weights": {"analytical_thinking": 25, "risk_tolerance": 15, "long_term_vision": 25}
                    }
                ]
            ),
            TestQuestion(
                id="extreme_q5",
                scenario="🤖 你獲得了一個「時光機」，可以回到過去任何一個投資時點。但只能使用一次，而且必須在24小時內決定。",
                question="你會選擇回到哪個歷史時刻？",
                options=[
                    {
                        "text": "📱 2007年買蘋果股票，iPhone即將改變世界",
                        "weights": {"long_term_vision": 30, "analytical_thinking": 25, "market_sensitivity": 15}
                    },
                    {
                        "text": "₿ 2010年買比特幣，1美元能買1300個",
                        "weights": {"risk_tolerance": 35, "market_sensitivity": 25, "analytical_thinking": 10}
                    },
                    {
                        "text": "🏠 1990年買台北精華區房地產",
                        "weights": {"long_term_vision": 35, "risk_tolerance": 15, "analytical_thinking": 20}
                    },
                    {
                        "text": "🤔 不用時光機，專注現在的投資機會",
                        "weights": {"emotional_control": 30, "analytical_thinking": 25, "long_term_vision": 20}
                    }
                ]
            ),
            TestQuestion(
                id="extreme_q6",
                scenario="🎭 你發現你的投資顧問其實是個AI機器人，而且它剛剛承認在過去一年中有30%的建議是「隨機生成」的。但你跟著它的建議賺了50%。",
                question="得知真相後，你會？",
                options=[
                    {
                        "text": "🤖 繼續跟隨，結果比過程重要",
                        "weights": {"analytical_thinking": 15, "emotional_control": 20, "market_sensitivity": 10}
                    },
                    {
                        "text": "😡 立即換人，我被騙了一年！",
                        "weights": {"emotional_control": -15, "analytical_thinking": 10, "risk_tolerance": -10}
                    },
                    {
                        "text": "🧪 把它當實驗，觀察AI的投資邏輯",
                        "weights": {"analytical_thinking": 30, "long_term_vision": 20, "market_sensitivity": 15}
                    },
                    {
                        "text": "🎲 既然有隨機成分，我自己丟骰子決定",
                        "weights": {"risk_tolerance": 20, "emotional_control": -5, "analytical_thinking": -10}
                    }
                ]
            ),
            TestQuestion(
                id="extreme_q7",
                scenario="🔮 一位神秘的「時間旅行者」聲稱來自2030年，告訴你未來5年的股市走勢。他的預測前3次都準確無誤，現在要收費100萬台幣。",
                question="面對這個「未來信息」，你會？",
                options=[
                    {
                        "text": "💰 借錢也要買！這是改變命運的機會",
                        "weights": {"risk_tolerance": 40, "analytical_thinking": -20, "emotional_control": -15}
                    },
                    {
                        "text": "🕵️ 調查他的身份和預測方法",
                        "weights": {"analytical_thinking": 35, "emotional_control": 20, "long_term_vision": 15}
                    },
                    {
                        "text": "🎯 小額測試，看看第4次預測是否準確",
                        "weights": {"analytical_thinking": 25, "risk_tolerance": 15, "emotional_control": 15}
                    },
                    {
                        "text": "🚫 完全不信，時間旅行是科幻小說",
                        "weights": {"analytical_thinking": 30, "emotional_control": 25, "long_term_vision": 20}
                    }
                ]
            ),
            TestQuestion(
                id="extreme_q8",
                scenario="💀 你最害怕的投資噩夢成真了：你把所有積蓄投入的「穩健基金」突然宣布投資了高風險衍生品，一夜間淨值歸零。",
                question="面對這個毀滅性打擊，你會？",
                options=[
                    {
                        "text": "⚖️ 立即提告，要求賠償到底",
                        "weights": {"emotional_control": 10, "analytical_thinking": 20, "risk_tolerance": -10}
                    },
                    {
                        "text": "💪 重新開始，這次更謹慎地投資",
                        "weights": {"emotional_control": 30, "long_term_vision": 25, "analytical_thinking": 20}
                    },
                    {
                        "text": "🏦 從此只存銀行定存，再也不投資",
                        "weights": {"risk_tolerance": -30, "emotional_control": -10, "long_term_vision": -15}
                    },
                    {
                        "text": "📚 深入學習投資知識，避免再次受騙",
                        "weights": {"analytical_thinking": 35, "long_term_vision": 30, "emotional_control": 20}
                    }
                ]
            )
        ]
        return questions
    
    def _load_viral_elements(self) -> Dict[str, Any]:
        """載入病毒式傳播元素"""
        return {
            "shock_factors": [
                "你的投資決策比99%的人更極端！",
                "你的風險承受度超越了華爾街交易員！",
                "你的投資心理年齡竟然是XX歲！",
                "你在極端市場中的表現讓巴菲特都要佩服！"
            ],
            "comparison_hooks": [
                "擊敗了{}%的投資者",
                "比{}%的專業交易員更冷靜",
                "風險承受度超越{}%的創業家",
                "在極端情況下比{}%的人更理性"
            ],
            "personality_reveals": {
                PersonalityType.COLD_HUNTER: {
                    "viral_title": "🦅 冷血獵手 - 市場掠食者",
                    "shock_description": "你是那種在別人恐慌時大舉買入的狠角色！當市場血流成河時，你看到的不是災難，而是千載難逢的獵食機會。",
                    "celebrity_match": "你的投資風格融合了索羅斯的狠辣和巴菲特的冷靜",
                    "extreme_trait": "在極端市場中，你的表現比95%的專業交易員更出色"
                },
                PersonalityType.WISE_ELDER: {
                    "viral_title": "🧙‍♂️ 智慧長者 - 時間的朋友",
                    "shock_description": "你擁有超越年齡的投資智慧！當別人被市場情緒左右時，你能看穿時間的迷霧，抓住真正的價值。",
                    "celebrity_match": "你的投資哲學接近查理·蒙格的深度思考",
                    "extreme_trait": "你的長期視野超越了90%的投資者"
                },
                PersonalityType.SENSITIVE_RADAR: {
                    "viral_title": "📡 敏感雷達 - 市場先知",
                    "shock_description": "你對市場變化的敏感度堪比地震儀！能在第一時間捕捉到市場的微妙變化，但有時也會被假信號干擾。",
                    "celebrity_match": "你的市場嗅覺類似彼得·林奇的敏銳直覺",
                    "extreme_trait": "你能比85%的分析師更早發現市場轉折點"
                },
                PersonalityType.BRAVE_WARRIOR: {
                    "viral_title": "⚔️ 勇敢戰士 - 無畏挑戰者",
                    "shock_description": "你是投資戰場上的勇士！敢於在最危險的時刻出手，追求最大的回報，但有時勇氣會變成魯莽。",
                    "celebrity_match": "你的投資勇氣媲美卡爾·伊坎的激進風格",
                    "extreme_trait": "你的風險承受度超越了80%的創業家"
                },
                PersonalityType.CAUTIOUS_GUARDIAN: {
                    "viral_title": "🛡️ 謹慎守護者 - 財富保衛戰",
                    "shock_description": "你是財富的忠實守護者！在投資的戰場上，你優先考慮的是保護而非攻擊，穩健勝過一切。",
                    "celebrity_match": "你的謹慎程度接近雷·達里奧的風險管理哲學",
                    "extreme_trait": "你的風險控制能力超越了75%的基金經理"
                },
                PersonalityType.EMOTIONAL_ROLLER: {
                    "viral_title": "🎢 情緒過山車 - 心跳投資者",
                    "shock_description": "你的投資情緒比雲霄飛車還刺激！市場的每一個波動都能牽動你的心弦，這讓你既能抓住機會，也容易錯失良機。",
                    "celebrity_match": "你的情緒波動類似吉姆·克拉默的激情風格",
                    "extreme_trait": "你的情緒反應比70%的散戶投資者更強烈"
                }
            }
        }
    
    async def generate_viral_result(self, session_id: str) -> Dict[str, Any]:
        """生成病毒式傳播結果"""
        try:
            # 獲取基本測試結果
            basic_result = await self.get_test_result(session_id)
            if not basic_result:
                return {}
            
            personality_type = PersonalityType(basic_result["personality_type"]["type"])
            viral_info = self.viral_elements["personality_reveals"][personality_type]
            
            # 計算極端指標
            extreme_scores = self._calculate_extreme_scores(basic_result["dimension_scores"])
            percentile = self._calculate_viral_percentile(extreme_scores)
            
            # 生成病毒式內容
            viral_result = {
                **basic_result,
                "viral_elements": {
                    "title": viral_info["viral_title"],
                    "shock_description": viral_info["shock_description"],
                    "celebrity_match": viral_info["celebrity_match"],
                    "extreme_trait": viral_info["extreme_trait"],
                    "percentile": percentile,
                    "comparison_text": f"擊敗了{percentile}%的投資者",
                    "extreme_scores": extreme_scores,
                    "share_hooks": self._generate_share_hooks(personality_type, percentile),
                    "challenge_friends": self._generate_challenge_text(personality_type)
                }
            }
            
            return viral_result
            
        except Exception as e:
            logger.error(f"生成病毒式結果失敗: {e}")
            return {}
    
    def _calculate_extreme_scores(self, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """計算極端化指標"""
        scores = {}
        
        # 風險極端度 (0-100)
        risk_score = dimension_scores.get("risk_tolerance", 50)
        if risk_score >= 80:
            scores["risk_level"] = "極度冒險"
            scores["risk_description"] = "你的風險承受度超越了95%的投資者！"
        elif risk_score <= 20:
            scores["risk_level"] = "極度保守"
            scores["risk_description"] = "你比90%的投資者更謹慎！"
        else:
            scores["risk_level"] = "平衡"
            scores["risk_description"] = "你的風險控制恰到好處"
        
        # 情緒控制極端度
        emotion_score = dimension_scores.get("emotional_control", 50)
        if emotion_score >= 85:
            scores["emotion_level"] = "冰山"
            scores["emotion_description"] = "你的情緒控制力比98%的交易員更強！"
        elif emotion_score <= 15:
            scores["emotion_level"] = "火山"
            scores["emotion_description"] = "你的情緒反應比80%的散戶更激烈！"
        else:
            scores["emotion_level"] = "正常"
            scores["emotion_description"] = "你的情緒管理能力不錯"
        
        # 分析能力極端度
        analysis_score = dimension_scores.get("analytical_thinking", 50)
        if analysis_score >= 85:
            scores["analysis_level"] = "超級大腦"
            scores["analysis_description"] = "你的分析能力超越了92%的專業分析師！"
        elif analysis_score <= 15:
            scores["analysis_level"] = "直覺派"
            scores["analysis_description"] = "你比75%的投資者更依賴直覺！"
        else:
            scores["analysis_level"] = "理性"
            scores["analysis_description"] = "你的分析能力很均衡"
        
        return scores
    
    def _calculate_viral_percentile(self, extreme_scores: Dict[str, Any]) -> int:
        """計算病毒式百分位數"""
        # 基於極端程度計算一個吸引人的百分位數
        extreme_count = 0
        
        if "極度" in extreme_scores.get("risk_level", ""):
            extreme_count += 1
        if extreme_scores.get("emotion_level") in ["冰山", "火山"]:
            extreme_count += 1
        if extreme_scores.get("analysis_level") in ["超級大腦", "直覺派"]:
            extreme_count += 1
        
        # 根據極端程度返回不同的百分位數
        if extreme_count >= 3:
            return 95 + (hash(str(extreme_scores)) % 5)  # 95-99%
        elif extreme_count >= 2:
            return 85 + (hash(str(extreme_scores)) % 10)  # 85-94%
        elif extreme_count >= 1:
            return 70 + (hash(str(extreme_scores)) % 15)  # 70-84%
        else:
            return 50 + (hash(str(extreme_scores)) % 30)  # 50-79%
    
    def _generate_share_hooks(self, personality_type: PersonalityType, percentile: int) -> List[str]:
        """生成分享鉤子"""
        hooks = [
            f"我是{self.viral_elements['personality_reveals'][personality_type]['viral_title']}！",
            f"擊敗了{percentile}%的投資者！你敢來挑戰嗎？",
            "這個極端市場測試太準了，快來測測你的投資人格！",
            f"沒想到我在投資上竟然是這種類型...你呢？"
        ]
        return hooks
    
    def _generate_challenge_text(self, personality_type: PersonalityType) -> str:
        """生成挑戰朋友的文案"""
        challenges = {
            PersonalityType.COLD_HUNTER: "我是冷血獵手，在極端市場中獵食機會！你敢來比比誰更狠嗎？",
            PersonalityType.WISE_ELDER: "我是智慧長者，能看穿市場迷霧！你的投資智慧能超越我嗎？",
            PersonalityType.SENSITIVE_RADAR: "我是敏感雷達，能預測市場變化！你的直覺有我準嗎？",
            PersonalityType.BRAVE_WARRIOR: "我是勇敢戰士，敢在最危險時出手！你有這個膽量嗎？",
            PersonalityType.CAUTIOUS_GUARDIAN: "我是謹慎守護者，能完美控制風險！你能做得更好嗎？",
            PersonalityType.EMOTIONAL_ROLLER: "我是情緒過山車，投資充滿激情！你的心臟夠強嗎？"
        }
        return challenges.get(personality_type, "快來測測你的投資人格，看看能不能超越我！")