"""
Enterprise Brochure Generator - Data Models
Uses Pydantic v2 for 100% type-safe structured data extraction.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class CompanyOverview(BaseModel):
    """Core company identity and mission statement."""
    name: str = Field(description="Official name of the company or enterprise.")
    tagline: Optional[str] = Field(None, description="Catchy tagline or slogan.")
    mission_statement: str = Field(
        description="Core mission, purpose, or elevator pitch explaining what the enterprise does."
    )
    headquarters: Optional[str] = Field(None, description="Location of the headquarters if stated.")
    founded_year: Optional[int] = Field(None, description="Year the company was founded.")


class TargetAudience(BaseModel):
    """Target market, buyer personas, and problem-solution fit."""
    primary_industries: List[str] = Field(
        default_factory=list,
        description="Target industries (e.g., FinTech, Healthcare, Enterprise B2B SaaS)."
    )
    ideal_customer_profile: str = Field(
        description="Description of the ideal customer (e.g., CTOs, SMBs, Enterprise IT)."
    )
    core_pain_points: List[str] = Field(
        default_factory=list,
        description="Key business pain points that this enterprise solves."
    )


class ProductService(BaseModel):
    """Detailed information about an individual product or service offering."""
    name: str = Field(description="Name of the product, tool, or service.")
    category: str = Field(description="Category (e.g., Cloud Infrastructure, Consulting, AI Tool).")
    description: str = Field(description="Comprehensive summary of what this product/service does.")
    key_features: List[str] = Field(
        default_factory=list,
        description="Bullet points of the most prominent features or capabilities."
    )
    target_use_case: Optional[str] = Field(
        None, description="Primary real-world scenario or use case."
    )


class PricingTier(BaseModel):
    """Pricing structure or subscription model."""
    tier_name: str = Field(description="Name of the plan (e.g., Free, Starter, Pro, Enterprise).")
    price_info: str = Field(description="Pricing details (e.g., '$49/month', 'Contact Sales', 'Custom').")
    billing_period: Optional[str] = Field(None, description="Monthly, Annual, or One-time.")
    highlights: List[str] = Field(
        default_factory=list,
        description="Top features included in this pricing tier."
    )


class KeyDifferentiator(BaseModel):
    """Competitive advantage and unique value proposition (UVP)."""
    differentiator: str = Field(description="Unique capability or edge over competitors.")
    business_impact: str = Field(description="Measurable benefit or ROI delivered to the client.")


class ContactAndCTA(BaseModel):
    """Conversion mechanism, links, and contact channels."""
    primary_cta: str = Field(
        description="Main Call To Action (e.g., 'Book a Demo', 'Start 14-Day Free Trial')."
    )
    contact_email: Optional[str] = Field(None, description="Sales or support email address.")
    contact_phone: Optional[str] = Field(None, description="Contact phone number if available.")
    demo_or_signup_url: Optional[str] = Field(
        None, description="Direct URL for booking a demo or signing up."
    )


class EnterpriseBrochure(BaseModel):
    """
    Root Schema: Complete, production-ready enterprise brochure document.
    """
    company: CompanyOverview = Field(description="Core company identity and background.")
    target_audience: TargetAudience = Field(description="Target market and pain points addressed.")
    offerings: List[ProductService] = Field(
        default_factory=list,
        min_length=1,
        description="List of core products, solutions, or services offered."
    )
    key_differentiators: List[KeyDifferentiator] = Field(
        default_factory=list,
        description="Why clients choose this enterprise over alternatives."
    )
    pricing: List[PricingTier] = Field(
        default_factory=list,
        description="Identified pricing tiers or engagement models."
    )
    contact_and_cta: ContactAndCTA = Field(description="Next steps and call to action.")
    summary_verdict: str = Field(
        description="Executive summary synthesizing why this business stands out in the market."
    )

    @field_validator("offerings")
    @classmethod
    def validate_offerings(cls, v: List[ProductService]) -> List[ProductService]:
        """Self-healing validator: ensures at least one offering exists."""
        if not v:
            raise ValueError("At least one product or service offering must be extracted.")
        return v
