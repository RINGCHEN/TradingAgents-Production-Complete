"""
Community Platform
Social learning and collaboration features for TradingAgents ecosystem
Task 4.4.4: 社群功能建設

Features:
- Community forums and discussions
- Knowledge sharing and tutorials
- User-generated content and strategies
- Expert insights and mentorship
- Social trading and collaboration
- Reputation and achievement system
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import uuid
from abc import ABC, abstractmethod

class UserRole(Enum):
    NEWCOMER = "newcomer"
    MEMBER = "member"
    CONTRIBUTOR = "contributor"
    EXPERT = "expert"
    MODERATOR = "moderator"
    MENTOR = "mentor"
    ADMINISTRATOR = "administrator"

class ContentType(Enum):
    FORUM_POST = "forum_post"
    TUTORIAL = "tutorial"
    STRATEGY = "strategy"
    ANALYSIS = "analysis"
    Q_AND_A = "q_and_a"
    MARKET_INSIGHT = "market_insight"
    CODE_SNIPPET = "code_snippet"
    EDUCATIONAL_CONTENT = "educational_content"

class InteractionType(Enum):
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    FOLLOW = "follow"
    BOOKMARK = "bookmark"
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    ENDORSE = "endorse"

class AchievementCategory(Enum):
    CONTRIBUTION = "contribution"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    COMMUNITY_SUPPORT = "community_support"
    EXPERTISE = "expertise"
    MENTORSHIP = "mentorship"
    INNOVATION = "innovation"
    COLLABORATION = "collaboration"

@dataclass
class CommunityUser:
    """Community user profile"""
    user_id: str
    username: str
    display_name: str
    email: str
    role: UserRole
    bio: Optional[str]
    expertise_areas: List[str]
    location: Optional[str]
    social_links: Dict[str, str]
    reputation_score: int
    contribution_points: int
    achievements: List[str]
    joined_date: datetime
    last_activity: datetime
    status: str = "active"
    is_verified: bool = False

@dataclass
class CommunityContent:
    """Community content item"""
    content_id: str
    author_id: str
    content_type: ContentType
    title: str
    content: str
    tags: List[str]
    category: str
    attachments: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    engagement_metrics: Dict[str, int]
    status: str = "published"
    is_featured: bool = False
    is_pinned: bool = False

@dataclass
class ForumDiscussion:
    """Forum discussion thread"""
    discussion_id: str
    forum_category: str
    title: str
    initial_post_id: str
    author_id: str
    participants: Set[str]
    posts_count: int
    views_count: int
    last_activity: datetime
    tags: List[str]
    is_solved: bool
    is_locked: bool
    is_sticky: bool
    created_at: datetime

@dataclass
class CommunityInteraction:
    """User interaction with content"""
    interaction_id: str
    user_id: str
    target_id: str  # content_id or user_id
    interaction_type: InteractionType
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class MentorshipProgram:
    """Mentorship program details"""
    program_id: str
    mentor_id: str
    mentee_ids: List[str]
    program_name: str
    focus_areas: List[str]
    duration_weeks: int
    meeting_schedule: str
    progress_milestones: List[Dict[str, Any]]
    start_date: datetime
    end_date: datetime
    status: str = "active"

@dataclass
class Achievement:
    """Community achievement definition"""
    achievement_id: str
    name: str
    description: str
    category: AchievementCategory
    criteria: Dict[str, Any]
    badge_icon: str
    points_reward: int
    rarity_level: str  # common, uncommon, rare, epic, legendary
    is_recurring: bool
    created_at: datetime

class ReputationSystem:
    """Manages user reputation and scoring"""
    
    def __init__(self):
        self.reputation_scores = {}
        self.reputation_history = {}
        self.scoring_rules = self._initialize_scoring_rules()
    
    def _initialize_scoring_rules(self) -> Dict[str, int]:
        """Initialize reputation scoring rules"""
        
        return {
            # Content creation
            "create_tutorial": 50,
            "create_strategy": 40,
            "create_analysis": 30,
            "create_forum_post": 10,
            "create_code_snippet": 20,
            
            # Engagement
            "receive_like": 2,
            "receive_upvote": 5,
            "receive_comment": 3,
            "receive_share": 10,
            "receive_endorse": 15,
            
            # Community participation
            "helpful_answer": 25,
            "solved_question": 30,
            "first_contribution": 20,
            "consistent_participation": 10,
            
            # Quality indicators
            "featured_content": 100,
            "expert_verification": 200,
            "mentor_feedback": 50,
            
            # Penalties
            "content_removed": -20,
            "warning_received": -10,
            "spam_reported": -50
        }
    
    async def update_reputation(
        self,
        user_id: str,
        action: str,
        context: Dict[str, Any] = None
    ) -> int:
        """Update user reputation based on action"""
        
        if user_id not in self.reputation_scores:
            self.reputation_scores[user_id] = 0
            self.reputation_history[user_id] = []
        
        points_change = self.scoring_rules.get(action, 0)
        
        # Apply multipliers based on context
        if context:
            # Expertise area bonus
            if context.get("expertise_match"):
                points_change = int(points_change * 1.5)
            
            # Community reaction bonus
            if context.get("high_engagement"):
                points_change = int(points_change * 1.2)
            
            # Quality bonus
            if context.get("verified_content"):
                points_change = int(points_change * 1.3)
        
        # Update reputation
        old_score = self.reputation_scores[user_id]
        new_score = max(0, old_score + points_change)
        self.reputation_scores[user_id] = new_score
        
        # Record history
        self.reputation_history[user_id].append({
            "action": action,
            "points_change": points_change,
            "old_score": old_score,
            "new_score": new_score,
            "timestamp": datetime.now(timezone.utc),
            "context": context or {}
        })
        
        return new_score
    
    def get_user_level(self, reputation_score: int) -> Tuple[str, int]:
        """Get user level based on reputation score"""
        
        levels = [
            (0, "Newcomer", 1),
            (100, "Contributor", 2),
            (500, "Regular", 3),
            (1500, "Expert", 4),
            (5000, "Master", 5),
            (15000, "Guru", 6),
            (50000, "Legend", 7)
        ]
        
        for i, (threshold, level_name, level_num) in enumerate(levels):
            if reputation_score < threshold:
                if i == 0:
                    return level_name, level_num
                prev_threshold, prev_name, prev_num = levels[i-1]
                return prev_name, prev_num
        
        return levels[-1][1], levels[-1][2]

class ContentModerationSystem:
    """Manages content moderation and quality control"""
    
    def __init__(self):
        self.moderation_queue = {}
        self.moderation_rules = {}
        self.moderator_assignments = {}
        self._initialize_moderation_rules()
    
    def _initialize_moderation_rules(self):
        """Initialize content moderation rules"""
        
        self.moderation_rules = {
            "spam_detection": {
                "enabled": True,
                "keywords": ["spam", "scam", "get rich quick", "guaranteed profit"],
                "pattern_checks": True,
                "ai_detection": True
            },
            "quality_threshold": {
                "min_content_length": 50,
                "require_tags": True,
                "require_category": True,
                "ai_quality_check": True
            },
            "community_guidelines": {
                "no_financial_advice": True,
                "respectful_communication": True,
                "no_personal_attacks": True,
                "factual_accuracy": True
            },
            "auto_moderation": {
                "flag_suspicious_content": True,
                "hold_new_user_content": True,
                "detect_duplicate_content": True
            }
        }
    
    async def moderate_content(self, content: CommunityContent) -> Dict[str, Any]:
        """Moderate content based on community guidelines"""
        
        moderation_result = {
            "content_id": content.content_id,
            "approved": True,
            "flags": [],
            "score": 100,
            "actions_required": [],
            "moderator_review_needed": False
        }
        
        # Check spam detection
        if self._contains_spam_indicators(content.content):
            moderation_result["flags"].append("potential_spam")
            moderation_result["score"] -= 50
            moderation_result["approved"] = False
        
        # Check quality threshold
        if len(content.content) < self.moderation_rules["quality_threshold"]["min_content_length"]:
            moderation_result["flags"].append("insufficient_content")
            moderation_result["score"] -= 20
        
        # Check for tags and categorization
        if not content.tags and self.moderation_rules["quality_threshold"]["require_tags"]:
            moderation_result["flags"].append("missing_tags")
            moderation_result["score"] -= 10
        
        # AI quality assessment (mock)
        ai_quality_score = self._ai_quality_assessment(content)
        if ai_quality_score < 70:
            moderation_result["flags"].append("low_quality_content")
            moderation_result["score"] -= 30
        
        # Financial advice detection
        if self._contains_financial_advice(content.content):
            moderation_result["flags"].append("potential_financial_advice")
            moderation_result["actions_required"].append("add_disclaimer")
            moderation_result["moderator_review_needed"] = True
        
        # Final approval decision
        if moderation_result["score"] < 60 or len(moderation_result["flags"]) >= 3:
            moderation_result["approved"] = False
            moderation_result["moderator_review_needed"] = True
        
        return moderation_result
    
    def _contains_spam_indicators(self, content: str) -> bool:
        """Check if content contains spam indicators"""
        
        spam_keywords = self.moderation_rules["spam_detection"]["keywords"]
        content_lower = content.lower()
        
        for keyword in spam_keywords:
            if keyword in content_lower:
                return True
        
        # Check for excessive repetition
        words = content_lower.split()
        if len(set(words)) < len(words) * 0.5:  # Less than 50% unique words
            return True
        
        return False
    
    def _ai_quality_assessment(self, content: CommunityContent) -> int:
        """AI-powered content quality assessment (mock)"""
        
        # Mock AI assessment based on content characteristics
        base_score = 70
        
        # Length bonus
        if len(content.content) > 500:
            base_score += 10
        
        # Structure bonus
        if any(char in content.content for char in ['\n', '.', ';']):
            base_score += 5
        
        # Tags bonus
        if len(content.tags) >= 3:
            base_score += 10
        
        # Code or technical content bonus
        if any(keyword in content.content.lower() for keyword in ['python', 'api', 'algorithm', 'strategy']):
            base_score += 15
        
        return min(100, base_score)
    
    def _contains_financial_advice(self, content: str) -> bool:
        """Check if content contains financial advice"""
        
        advice_indicators = [
            "you should buy", "i recommend buying", "sell now",
            "guaranteed profit", "investment advice", "financial recommendation"
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in advice_indicators)

class KnowledgeBaseManager:
    """Manages community knowledge base and tutorials"""
    
    def __init__(self):
        self.knowledge_articles = {}
        self.tutorial_series = {}
        self.learning_paths = {}
        self.categories = self._initialize_categories()
    
    def _initialize_categories(self) -> Dict[str, Dict[str, Any]]:
        """Initialize knowledge base categories"""
        
        return {
            "getting_started": {
                "name": "Getting Started",
                "description": "Basic concepts and first steps",
                "difficulty": "beginner",
                "estimated_time": "2-4 hours",
                "prerequisites": []
            },
            "api_development": {
                "name": "API Development",
                "description": "Using TradingAgents APIs effectively",
                "difficulty": "intermediate",
                "estimated_time": "4-8 hours",
                "prerequisites": ["getting_started", "basic_programming"]
            },
            "trading_strategies": {
                "name": "Trading Strategies",
                "description": "Developing and implementing trading strategies",
                "difficulty": "advanced",
                "estimated_time": "8-16 hours",
                "prerequisites": ["api_development", "market_analysis"]
            },
            "market_analysis": {
                "name": "Market Analysis",
                "description": "Technical and fundamental analysis techniques",
                "difficulty": "intermediate",
                "estimated_time": "6-12 hours",
                "prerequisites": ["getting_started", "financial_concepts"]
            },
            "system_integration": {
                "name": "System Integration",
                "description": "Integrating TradingAgents with other systems",
                "difficulty": "advanced",
                "estimated_time": "12-20 hours",
                "prerequisites": ["api_development", "system_architecture"]
            }
        }
    
    async def create_tutorial(
        self,
        author_id: str,
        title: str,
        category: str,
        content: str,
        difficulty_level: str,
        prerequisites: List[str],
        estimated_time: str,
        attachments: List[Dict[str, Any]] = None
    ) -> CommunityContent:
        """Create new tutorial"""
        
        content_id = f"tutorial_{uuid.uuid4().hex[:8]}"
        
        tutorial = CommunityContent(
            content_id=content_id,
            author_id=author_id,
            content_type=ContentType.TUTORIAL,
            title=title,
            content=content,
            tags=[category, difficulty_level, "tutorial"],
            category=category,
            attachments=attachments or [],
            metadata={
                "difficulty_level": difficulty_level,
                "prerequisites": prerequisites,
                "estimated_time": estimated_time,
                "tutorial_type": "community_generated",
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            engagement_metrics={
                "views": 0,
                "likes": 0,
                "bookmarks": 0,
                "completions": 0,
                "ratings_sum": 0,
                "ratings_count": 0
            }
        )
        
        self.knowledge_articles[content_id] = tutorial
        return tutorial
    
    def create_learning_path(
        self,
        path_name: str,
        description: str,
        tutorials: List[str],
        target_audience: str,
        estimated_completion_time: str
    ) -> Dict[str, Any]:
        """Create structured learning path"""
        
        path_id = f"path_{uuid.uuid4().hex[:8]}"
        
        learning_path = {
            "path_id": path_id,
            "path_name": path_name,
            "description": description,
            "tutorials": tutorials,
            "target_audience": target_audience,
            "estimated_completion_time": estimated_completion_time,
            "difficulty_progression": "beginner_to_advanced",
            "completion_criteria": {
                "min_tutorials_completed": len(tutorials) * 0.8,  # 80% completion
                "min_average_rating": 4.0,
                "include_practical_exercises": True
            },
            "created_at": datetime.now(timezone.utc),
            "enrollments": 0,
            "completions": 0,
            "average_rating": 0.0
        }
        
        self.learning_paths[path_id] = learning_path
        return learning_path
    
    def get_personalized_recommendations(
        self, 
        user_id: str, 
        user_expertise: List[str],
        completed_tutorials: List[str]
    ) -> List[Dict[str, Any]]:
        """Get personalized learning recommendations"""
        
        recommendations = []
        
        for tutorial_id, tutorial in self.knowledge_articles.items():
            if tutorial_id in completed_tutorials:
                continue
            
            # Calculate relevance score
            relevance_score = 0
            
            # Expertise match
            tutorial_tags = tutorial.tags + [tutorial.category]
            expertise_overlap = set(user_expertise) & set(tutorial_tags)
            relevance_score += len(expertise_overlap) * 20
            
            # Difficulty appropriateness
            user_level = len(completed_tutorials) // 5  # Simple level calculation
            tutorial_difficulty = {"beginner": 1, "intermediate": 2, "advanced": 3}.get(
                tutorial.metadata.get("difficulty_level", "beginner"), 1
            )
            
            if abs(user_level - tutorial_difficulty) <= 1:
                relevance_score += 30
            
            # Popularity and quality
            engagement = tutorial.engagement_metrics
            if engagement["ratings_count"] > 0:
                avg_rating = engagement["ratings_sum"] / engagement["ratings_count"]
                relevance_score += avg_rating * 10
            
            if tutorial.is_featured:
                relevance_score += 25
            
            recommendations.append({
                "tutorial_id": tutorial_id,
                "title": tutorial.title,
                "category": tutorial.category,
                "difficulty": tutorial.metadata.get("difficulty_level"),
                "estimated_time": tutorial.metadata.get("estimated_time"),
                "relevance_score": relevance_score,
                "engagement_metrics": engagement
            })
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        return recommendations[:10]  # Return top 10 recommendations

class MentorshipSystem:
    """Manages mentorship programs and expert guidance"""
    
    def __init__(self):
        self.mentorship_programs = {}
        self.mentor_profiles = {}
        self.mentee_applications = {}
        self.matching_algorithm = MentorMenteeMatching()
    
    async def register_as_mentor(
        self,
        user_id: str,
        expertise_areas: List[str],
        experience_years: int,
        mentoring_capacity: int,
        availability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Register user as mentor"""
        
        mentor_id = f"mentor_{user_id}"
        
        mentor_profile = {
            "mentor_id": mentor_id,
            "user_id": user_id,
            "expertise_areas": expertise_areas,
            "experience_years": experience_years,
            "mentoring_capacity": mentoring_capacity,
            "current_mentees": 0,
            "availability": availability,
            "mentoring_style": "collaborative",  # Default
            "success_stories": [],
            "ratings": {
                "total_ratings": 0,
                "average_rating": 0.0,
                "rating_breakdown": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
            },
            "program_history": [],
            "certification_level": "community_mentor",
            "status": "active",
            "created_at": datetime.now(timezone.utc)
        }
        
        self.mentor_profiles[mentor_id] = mentor_profile
        
        return {
            "mentor_id": mentor_id,
            "status": "registered",
            "next_steps": [
                "Complete mentor profile setup",
                "Take mentor training course",
                "Wait for mentee matching",
                "Schedule first mentoring session"
            ],
            "mentoring_resources": {
                "mentor_handbook": "https://community.tradingagents.com/mentor-handbook",
                "training_materials": "https://community.tradingagents.com/mentor-training",
                "support_channel": "#mentor-support"
            }
        }
    
    async def apply_for_mentorship(
        self,
        user_id: str,
        learning_goals: List[str],
        current_skill_level: str,
        preferred_mentor_traits: List[str],
        time_commitment: str
    ) -> Dict[str, Any]:
        """Apply for mentorship program"""
        
        application_id = f"app_{uuid.uuid4().hex[:8]}"
        
        application = {
            "application_id": application_id,
            "user_id": user_id,
            "learning_goals": learning_goals,
            "current_skill_level": current_skill_level,
            "preferred_mentor_traits": preferred_mentor_traits,
            "time_commitment": time_commitment,
            "motivation_statement": "Looking to enhance trading skills with AI",  # Default
            "application_date": datetime.now(timezone.utc),
            "status": "pending_review",
            "matching_preferences": {
                "expertise_priority": learning_goals,
                "communication_style": "collaborative",
                "session_frequency": "weekly"
            }
        }
        
        self.mentee_applications[application_id] = application
        
        # Find potential mentors
        potential_mentors = await self.matching_algorithm.find_matching_mentors(
            application["learning_goals"],
            application["current_skill_level"],
            application["preferred_mentor_traits"]
        )
        
        return {
            "application_id": application_id,
            "status": "submitted",
            "potential_mentors_count": len(potential_mentors),
            "estimated_matching_time": "3-7 days",
            "next_steps": [
                "Application review process",
                "Mentor matching algorithm",
                "Introduction and first meeting",
                "Program kickoff"
            ],
            "mentee_resources": {
                "preparation_guide": "https://community.tradingagents.com/mentee-guide",
                "goal_setting_worksheet": "https://community.tradingagents.com/goal-worksheet",
                "support_channel": "#mentee-support"
            }
        }
    
    async def create_mentorship_program(
        self,
        mentor_id: str,
        mentee_id: str,
        program_focus: List[str],
        duration_weeks: int = 12
    ) -> MentorshipProgram:
        """Create new mentorship program"""
        
        program_id = f"program_{uuid.uuid4().hex[:8]}"
        
        # Create program milestones
        milestones = self._generate_program_milestones(program_focus, duration_weeks)
        
        program = MentorshipProgram(
            program_id=program_id,
            mentor_id=mentor_id,
            mentee_ids=[mentee_id],
            program_name=f"Mentorship Program: {' & '.join(program_focus[:2])}",
            focus_areas=program_focus,
            duration_weeks=duration_weeks,
            meeting_schedule="weekly_1hour",
            progress_milestones=milestones,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(weeks=duration_weeks)
        )
        
        self.mentorship_programs[program_id] = program
        
        return program
    
    def _generate_program_milestones(
        self, 
        focus_areas: List[str], 
        duration_weeks: int
    ) -> List[Dict[str, Any]]:
        """Generate program milestones based on focus areas"""
        
        milestones = []
        weeks_per_milestone = max(2, duration_weeks // 4)
        
        milestone_templates = {
            "api_development": [
                "Basic API integration",
                "Advanced API usage",
                "Custom implementation",
                "Production deployment"
            ],
            "trading_strategies": [
                "Strategy fundamentals",
                "Backtesting implementation",
                "Risk management integration",
                "Live trading preparation"
            ],
            "market_analysis": [
                "Analysis framework setup",
                "Technical indicators implementation",
                "Pattern recognition",
                "Automated analysis system"
            ]
        }
        
        for i, area in enumerate(focus_areas[:4]):  # Max 4 focus areas
            templates = milestone_templates.get(area, ["Basic concepts", "Intermediate application", "Advanced techniques", "Mastery project"])
            
            for j, template in enumerate(templates):
                week_target = (j + 1) * weeks_per_milestone
                if week_target <= duration_weeks:
                    milestones.append({
                        "milestone_id": f"ms_{i}_{j}",
                        "title": f"{area.title()}: {template}",
                        "description": f"Complete {template.lower()} for {area}",
                        "target_week": week_target,
                        "status": "pending",
                        "completion_criteria": [
                            "Demonstrate understanding",
                            "Complete practical exercise",
                            "Peer review or mentor approval"
                        ],
                        "resources": []
                    })
        
        return milestones

class MentorMenteeMatching:
    """Algorithm for matching mentors with mentees"""
    
    async def find_matching_mentors(
        self,
        learning_goals: List[str],
        skill_level: str,
        preferred_traits: List[str]
    ) -> List[Dict[str, Any]]:
        """Find mentors that match mentee requirements"""
        
        # Mock mentor pool
        mock_mentors = [
            {
                "mentor_id": "mentor_001",
                "expertise_areas": ["api_development", "python_programming"],
                "experience_years": 8,
                "mentoring_style": "hands_on",
                "availability": "high",
                "rating": 4.8,
                "current_mentees": 2,
                "capacity": 5
            },
            {
                "mentor_id": "mentor_002", 
                "expertise_areas": ["trading_strategies", "market_analysis"],
                "experience_years": 12,
                "mentoring_style": "collaborative",
                "availability": "medium",
                "rating": 4.9,
                "current_mentees": 3,
                "capacity": 4
            },
            {
                "mentor_id": "mentor_003",
                "expertise_areas": ["system_integration", "api_development"],
                "experience_years": 6,
                "mentoring_style": "structured",
                "availability": "high",
                "rating": 4.6,
                "current_mentees": 1,
                "capacity": 3
            }
        ]
        
        matches = []
        
        for mentor in mock_mentors:
            if mentor["current_mentees"] >= mentor["capacity"]:
                continue
            
            # Calculate match score
            score = 0
            
            # Expertise overlap
            expertise_overlap = set(learning_goals) & set(mentor["expertise_areas"])
            score += len(expertise_overlap) * 30
            
            # Availability
            if mentor["availability"] == "high":
                score += 20
            elif mentor["availability"] == "medium":
                score += 10
            
            # Rating
            score += mentor["rating"] * 10
            
            # Capacity utilization (prefer mentors with capacity)
            capacity_utilization = mentor["current_mentees"] / mentor["capacity"]
            if capacity_utilization < 0.8:
                score += 15
            
            # Style preference
            if mentor["mentoring_style"] in preferred_traits:
                score += 25
            
            matches.append({
                "mentor_id": mentor["mentor_id"],
                "match_score": score,
                "mentor_details": mentor,
                "matching_factors": {
                    "expertise_overlap": list(expertise_overlap),
                    "availability": mentor["availability"],
                    "rating": mentor["rating"],
                    "capacity_available": mentor["capacity"] - mentor["current_mentees"]
                }
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches

class CommunityPlatform:
    """Main community platform orchestrator"""
    
    def __init__(self):
        self.users = {}
        self.content = {}
        self.discussions = {}
        self.interactions = {}
        
        # Initialize subsystems
        self.reputation_system = ReputationSystem()
        self.moderation_system = ContentModerationSystem()
        self.knowledge_base = KnowledgeBaseManager()
        self.mentorship_system = MentorshipSystem()
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize platform
        self._initialize_platform()
    
    def _initialize_platform(self):
        """Initialize community platform"""
        
        # Create sample users
        self._create_sample_users()
        
        # Create sample content
        self._create_sample_content()
        
        # Initialize forum categories
        self._initialize_forum_categories()
    
    def _create_sample_users(self):
        """Create sample community users"""
        
        sample_users = [
            {
                "username": "ai_trader_pro",
                "display_name": "AI Trading Professional",
                "role": UserRole.EXPERT,
                "expertise_areas": ["algorithmic_trading", "machine_learning", "api_development"],
                "bio": "10+ years in algorithmic trading with deep AI expertise"
            },
            {
                "username": "market_analyst_jane",
                "display_name": "Jane Market Analyst", 
                "role": UserRole.CONTRIBUTOR,
                "expertise_areas": ["technical_analysis", "market_research", "trading_psychology"],
                "bio": "Professional market analyst with focus on Asian markets"
            },
            {
                "username": "coding_newbie",
                "display_name": "Learning to Code",
                "role": UserRole.NEWCOMER,
                "expertise_areas": ["python_basics"],
                "bio": "New to programming, excited to learn trading automation"
            },
            {
                "username": "fintech_mentor",
                "display_name": "FinTech Mentor",
                "role": UserRole.MENTOR,
                "expertise_areas": ["fintech", "system_architecture", "mentorship"],
                "bio": "Helping others build successful trading systems"
            }
        ]
        
        for user_data in sample_users:
            user_id = f"user_{uuid.uuid4().hex[:8]}"
            
            user = CommunityUser(
                user_id=user_id,
                username=user_data["username"],
                display_name=user_data["display_name"],
                email=f"{user_data['username']}@example.com",
                role=user_data["role"],
                bio=user_data["bio"],
                expertise_areas=user_data["expertise_areas"],
                location="Global",
                social_links={},
                reputation_score=100 if user_data["role"] != UserRole.NEWCOMER else 10,
                contribution_points=50 if user_data["role"] != UserRole.NEWCOMER else 5,
                achievements=[],
                joined_date=datetime.now(timezone.utc) - timedelta(days=30),
                last_activity=datetime.now(timezone.utc)
            )
            
            self.users[user_id] = user
            
            # Initialize reputation
            self.reputation_system.reputation_scores[user_id] = user.reputation_score
    
    def _create_sample_content(self):
        """Create sample community content"""
        
        sample_content = [
            {
                "title": "Getting Started with TradingAgents API",
                "content_type": ContentType.TUTORIAL,
                "category": "getting_started",
                "content": "Complete guide for beginners to start using TradingAgents API...",
                "tags": ["beginner", "api", "tutorial"]
            },
            {
                "title": "Advanced Portfolio Optimization Strategies",
                "content_type": ContentType.STRATEGY,
                "category": "trading_strategies", 
                "content": "Deep dive into modern portfolio optimization techniques...",
                "tags": ["advanced", "portfolio", "optimization"]
            },
            {
                "title": "Market Sentiment Analysis with AI",
                "content_type": ContentType.ANALYSIS,
                "category": "market_analysis",
                "content": "How to use AI for analyzing market sentiment from news and social media...",
                "tags": ["ai", "sentiment", "analysis"]
            }
        ]
        
        user_ids = list(self.users.keys())
        
        for i, content_data in enumerate(sample_content):
            content_id = f"content_{uuid.uuid4().hex[:8]}"
            author_id = user_ids[i % len(user_ids)]
            
            content = CommunityContent(
                content_id=content_id,
                author_id=author_id,
                content_type=content_data["content_type"],
                title=content_data["title"],
                content=content_data["content"],
                tags=content_data["tags"],
                category=content_data["category"],
                attachments=[],
                metadata={"featured": i == 0},  # First content is featured
                created_at=datetime.now(timezone.utc) - timedelta(days=10-i),
                updated_at=None,
                engagement_metrics={
                    "views": 150 + i*50,
                    "likes": 15 + i*5,
                    "comments": 8 + i*2,
                    "shares": 3 + i,
                    "bookmarks": 12 + i*3
                },
                is_featured=(i == 0)
            )
            
            self.content[content_id] = content
    
    def _initialize_forum_categories(self):
        """Initialize forum discussion categories"""
        
        self.forum_categories = {
            "general_discussion": {
                "name": "General Discussion",
                "description": "General community discussions",
                "post_count": 245,
                "active_today": 12
            },
            "api_help": {
                "name": "API Help & Support",
                "description": "Get help with TradingAgents API",
                "post_count": 189,
                "active_today": 8
            },
            "strategy_sharing": {
                "name": "Strategy Sharing",
                "description": "Share and discuss trading strategies",
                "post_count": 156,
                "active_today": 15
            },
            "showcase": {
                "name": "Project Showcase", 
                "description": "Show off your projects and implementations",
                "post_count": 98,
                "active_today": 5
            },
            "market_insights": {
                "name": "Market Insights",
                "description": "Share market analysis and insights",
                "post_count": 134,
                "active_today": 9
            }
        }
    
    async def create_user_account(
        self,
        username: str,
        display_name: str,
        email: str,
        expertise_areas: List[str] = None,
        bio: str = None
    ) -> CommunityUser:
        """Create new community user account"""
        
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        
        user = CommunityUser(
            user_id=user_id,
            username=username,
            display_name=display_name,
            email=email,
            role=UserRole.NEWCOMER,
            bio=bio,
            expertise_areas=expertise_areas or [],
            location=None,
            social_links={},
            reputation_score=10,  # Starting reputation
            contribution_points=0,
            achievements=["first_join"],
            joined_date=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        
        self.users[user_id] = user
        
        # Initialize reputation
        self.reputation_system.reputation_scores[user_id] = 10
        await self.reputation_system.update_reputation(user_id, "first_contribution")
        
        return user
    
    async def post_content(
        self,
        author_id: str,
        content_type: ContentType,
        title: str,
        content: str,
        category: str,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Post new content to community"""
        
        content_id = f"content_{uuid.uuid4().hex[:8]}"
        
        community_content = CommunityContent(
            content_id=content_id,
            author_id=author_id,
            content_type=content_type,
            title=title,
            content=content,
            tags=tags or [],
            category=category,
            attachments=[],
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            engagement_metrics={
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "bookmarks": 0
            }
        )
        
        # Moderate content
        moderation_result = await self.moderation_system.moderate_content(community_content)
        
        if moderation_result["approved"]:
            self.content[content_id] = community_content
            
            # Update author reputation
            reputation_action = f"create_{content_type.value}"
            await self.reputation_system.update_reputation(author_id, reputation_action)
            
            return {
                "content_id": content_id,
                "status": "published",
                "moderation_score": moderation_result["score"],
                "visibility": "public"
            }
        else:
            return {
                "content_id": content_id,
                "status": "pending_moderation",
                "moderation_flags": moderation_result["flags"],
                "actions_required": moderation_result["actions_required"],
                "review_needed": moderation_result["moderator_review_needed"]
            }
    
    async def interact_with_content(
        self,
        user_id: str,
        content_id: str,
        interaction_type: InteractionType,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """User interaction with content"""
        
        if content_id not in self.content:
            return {"error": "Content not found"}
        
        interaction_id = f"int_{uuid.uuid4().hex[:8]}"
        
        interaction = CommunityInteraction(
            interaction_id=interaction_id,
            user_id=user_id,
            target_id=content_id,
            interaction_type=interaction_type,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc)
        )
        
        self.interactions[interaction_id] = interaction
        
        # Update content engagement metrics
        content = self.content[content_id]
        metric_key = interaction_type.value + "s" if not interaction_type.value.endswith("e") else interaction_type.value[:-1] + "s"
        
        if metric_key in content.engagement_metrics:
            content.engagement_metrics[metric_key] += 1
        
        # Update reputation for content author
        author_id = content.author_id
        reputation_action = f"receive_{interaction_type.value}"
        await self.reputation_system.update_reputation(author_id, reputation_action)
        
        return {
            "interaction_id": interaction_id,
            "status": "recorded",
            "updated_metrics": content.engagement_metrics
        }
    
    def get_community_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get personalized community dashboard"""
        
        user = self.users.get(user_id)
        if not user:
            return {"error": "User not found"}
        
        # Get user's content
        user_content = [c for c in self.content.values() if c.author_id == user_id]
        
        # Get learning recommendations
        completed_tutorials = [c.content_id for c in user_content if c.content_type == ContentType.TUTORIAL]
        recommendations = self.knowledge_base.get_personalized_recommendations(
            user_id, user.expertise_areas, completed_tutorials
        )
        
        # Get user level
        level_name, level_num = self.reputation_system.get_user_level(user.reputation_score)
        
        # Calculate activity metrics
        recent_interactions = [
            i for i in self.interactions.values() 
            if i.user_id == user_id and i.timestamp > datetime.now(timezone.utc) - timedelta(days=30)
        ]
        
        dashboard = {
            "user_profile": {
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role.value,
                "level": {"name": level_name, "number": level_num},
                "reputation_score": user.reputation_score,
                "contribution_points": user.contribution_points,
                "expertise_areas": user.expertise_areas,
                "achievements_count": len(user.achievements)
            },
            "activity_summary": {
                "content_created": len(user_content),
                "recent_interactions": len(recent_interactions),
                "total_content_views": sum(c.engagement_metrics.get("views", 0) for c in user_content),
                "total_content_likes": sum(c.engagement_metrics.get("likes", 0) for c in user_content)
            },
            "learning_progress": {
                "tutorials_completed": len(completed_tutorials),
                "recommended_content": recommendations[:5],
                "learning_streak_days": 7,  # Mock data
                "next_level_progress": min(100, (user.reputation_score % 500) / 5)
            },
            "community_engagement": {
                "forum_discussions_participated": len([i for i in recent_interactions if i.interaction_type == InteractionType.COMMENT]),
                "content_shared": len([i for i in recent_interactions if i.interaction_type == InteractionType.SHARE]),
                "users_helped": 3,  # Mock data
                "mentor_status": user.role in [UserRole.MENTOR, UserRole.EXPERT]
            },
            "recent_activity": [
                {
                    "date": "2025-08-10",
                    "activity": "Posted new tutorial",
                    "details": "Advanced API Integration Patterns"
                },
                {
                    "date": "2025-08-09", 
                    "activity": "Received expert endorsement",
                    "details": "AI Trading Strategy analysis"
                },
                {
                    "date": "2025-08-08",
                    "activity": "Completed learning path",
                    "details": "Market Analysis Fundamentals"
                }
            ],
            "upcoming_events": [
                {
                    "date": "2025-08-15",
                    "event": "Community Webinar",
                    "details": "Advanced Trading Strategies with AI"
                },
                {
                    "date": "2025-08-20",
                    "event": "Mentorship Session",
                    "details": "Weekly one-on-one with mentor"
                }
            ]
        }
        
        return dashboard
    
    def get_platform_analytics(self) -> Dict[str, Any]:
        """Get comprehensive community platform analytics"""
        
        total_users = len(self.users)
        active_users = len([u for u in self.users.values() if u.status == "active"])
        
        # Content metrics
        total_content = len(self.content)
        content_by_type = {}
        
        for content in self.content.values():
            content_type = content.content_type.value
            content_by_type[content_type] = content_by_type.get(content_type, 0) + 1
        
        # Engagement metrics
        total_interactions = len(self.interactions)
        recent_interactions = len([
            i for i in self.interactions.values() 
            if i.timestamp > datetime.now(timezone.utc) - timedelta(days=7)
        ])
        
        # User role distribution
        role_distribution = {}
        for user in self.users.values():
            role = user.role.value
            role_distribution[role] = role_distribution.get(role, 0) + 1
        
        analytics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "community_overview": {
                "total_users": total_users,
                "active_users": active_users,
                "user_role_distribution": role_distribution,
                "verified_experts": len([u for u in self.users.values() if u.is_verified])
            },
            "content_metrics": {
                "total_content_pieces": total_content,
                "content_by_type": content_by_type,
                "featured_content": len([c for c in self.content.values() if c.is_featured]),
                "total_content_views": sum(c.engagement_metrics.get("views", 0) for c in self.content.values())
            },
            "engagement_metrics": {
                "total_interactions": total_interactions,
                "recent_interactions_7d": recent_interactions,
                "average_content_engagement": total_interactions / total_content if total_content > 0 else 0,
                "top_contributors": self._get_top_contributors(5)
            },
            "knowledge_base_metrics": {
                "total_tutorials": len(self.knowledge_base.knowledge_articles),
                "learning_paths": len(self.knowledge_base.learning_paths),
                "categories": len(self.knowledge_base.categories)
            },
            "mentorship_metrics": {
                "active_mentors": len(self.mentorship_system.mentor_profiles),
                "active_programs": len(self.mentorship_system.mentorship_programs),
                "pending_applications": len([
                    app for app in self.mentorship_system.mentee_applications.values()
                    if app["status"] == "pending_review"
                ])
            },
            "forum_metrics": {
                "total_categories": len(self.forum_categories),
                "total_discussions": sum(cat["post_count"] for cat in self.forum_categories.values()),
                "active_discussions_today": sum(cat["active_today"] for cat in self.forum_categories.values())
            }
        }
        
        return analytics
    
    def _get_top_contributors(self, limit: int) -> List[Dict[str, Any]]:
        """Get top contributors by reputation score"""
        
        contributors = []
        
        for user in self.users.values():
            user_content = [c for c in self.content.values() if c.author_id == user.user_id]
            total_engagement = sum(
                sum(c.engagement_metrics.values()) for c in user_content
            )
            
            contributors.append({
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "reputation_score": user.reputation_score,
                "content_count": len(user_content),
                "total_engagement": total_engagement
            })
        
        contributors.sort(key=lambda x: x["reputation_score"], reverse=True)
        return contributors[:limit]

# Example usage and testing
if __name__ == "__main__":
    async def test_community_platform():
        platform = CommunityPlatform()
        
        print("Testing Community Platform...")
        
        # Test user account creation
        print("\n1. Testing User Account Creation:")
        new_user = await platform.create_user_account(
            "trading_enthusiast",
            "Trading Enthusiast",
            "enthusiast@example.com",
            ["api_development", "algorithmic_trading"],
            "Passionate about automated trading systems"
        )
        
        print(f"User created: {new_user.username} ({new_user.user_id})")
        print(f"Initial reputation: {new_user.reputation_score}")
        print(f"Expertise areas: {', '.join(new_user.expertise_areas)}")
        
        # Test content posting
        print("\n2. Testing Content Posting:")
        content_result = await platform.post_content(
            new_user.user_id,
            ContentType.TUTORIAL,
            "Building Your First Trading Bot",
            "Step-by-step guide to building a simple trading bot using TradingAgents API. This tutorial covers API authentication, data retrieval, signal generation, and basic risk management...",
            "getting_started",
            ["beginner", "tutorial", "trading_bot", "api"]
        )
        
        print(f"Content status: {content_result['status']}")
        if content_result['status'] == 'published':
            print(f"Content ID: {content_result['content_id']}")
            print(f"Moderation score: {content_result['moderation_score']}")
        
        # Test content interaction
        print("\n3. Testing Content Interaction:")
        existing_content_id = list(platform.content.keys())[0]
        interaction_result = await platform.interact_with_content(
            new_user.user_id,
            existing_content_id,
            InteractionType.LIKE
        )
        
        print(f"Interaction recorded: {interaction_result['status']}")
        print(f"Updated metrics: {interaction_result['updated_metrics']}")
        
        # Test mentorship application
        print("\n4. Testing Mentorship Application:")
        mentorship_result = await platform.mentorship_system.apply_for_mentorship(
            new_user.user_id,
            ["api_development", "trading_strategies"],
            "beginner",
            ["patient", "experienced", "collaborative"],
            "5_hours_per_week"
        )
        
        print(f"Application status: {mentorship_result['status']}")
        print(f"Potential mentors: {mentorship_result['potential_mentors_count']}")
        print(f"Estimated matching time: {mentorship_result['estimated_matching_time']}")
        
        # Test knowledge base tutorial creation
        print("\n5. Testing Tutorial Creation:")
        tutorial = await platform.knowledge_base.create_tutorial(
            new_user.user_id,
            "Advanced Portfolio Rebalancing Strategies",
            "trading_strategies",
            "Learn advanced techniques for portfolio rebalancing using AI-driven insights...",
            "intermediate",
            ["basic_portfolio_management", "api_development"],
            "3-4 hours"
        )
        
        print(f"Tutorial created: {tutorial.title}")
        print(f"Difficulty level: {tutorial.metadata['difficulty_level']}")
        print(f"Estimated time: {tutorial.metadata['estimated_time']}")
        
        # Test personalized recommendations
        print("\n6. Testing Learning Recommendations:")
        recommendations = platform.knowledge_base.get_personalized_recommendations(
            new_user.user_id,
            new_user.expertise_areas,
            []  # No completed tutorials yet
        )
        
        print(f"Recommendations found: {len(recommendations)}")
        for i, rec in enumerate(recommendations[:3]):
            print(f"  {i+1}. {rec['title']} (Relevance: {rec['relevance_score']:.0f})")
        
        # Test community dashboard
        print("\n7. Testing Community Dashboard:")
        dashboard = platform.get_community_dashboard(new_user.user_id)
        
        print(f"User level: {dashboard['user_profile']['level']['name']} (Level {dashboard['user_profile']['level']['number']})")
        print(f"Reputation score: {dashboard['user_profile']['reputation_score']}")
        print(f"Content created: {dashboard['activity_summary']['content_created']}")
        print(f"Learning recommendations: {len(dashboard['learning_progress']['recommended_content'])}")
        
        # Get platform analytics
        print("\n8. Platform Analytics:")
        analytics = platform.get_platform_analytics()
        
        print(f"Total users: {analytics['community_overview']['total_users']}")
        print(f"Total content: {analytics['content_metrics']['total_content_pieces']}")
        print(f"Total interactions: {analytics['engagement_metrics']['total_interactions']}")
        print(f"Active mentors: {analytics['mentorship_metrics']['active_mentors']}")
        print(f"Forum discussions: {analytics['forum_metrics']['total_discussions']}")
        
        print(f"\nTop contributors:")
        for contributor in analytics['engagement_metrics']['top_contributors']:
            print(f"  - {contributor['display_name']}: {contributor['reputation_score']} reputation")
        
        return platform
    
    # Run test
    platform = asyncio.run(test_community_platform())
    print("\nCommunity Platform test completed successfully!")