from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from app.schemas.common import BaseResponse, DataResponse


class TokenData(BaseModel):
    """JWT token data"""
    user_id: str = Field(description="User ID")
    email: str = Field(description="User email")
    is_superuser: bool = Field(default=False, description="Whether user is superuser")
    exp: Optional[int] = Field(None, description="Token expiration timestamp")


class Token(BaseModel):
    """JWT token response"""
    access_token: str = Field(description="Access token")
    refresh_token: str = Field(description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Whether to remember the user")


class LoginResponse(DataResponse[Token]):
    """Login response schema"""
    data: Token = Field(description="Authentication tokens")
    user: "UserResponse" = Field(description="User information")


class RegisterRequest(BaseModel):
    """User registration request schema"""
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Username (alphanumeric, underscore, hyphen only)"
    )
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, description="User password")
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_number:
            raise ValueError('Password must contain at least one number')
        
        return v


class RegisterResponse(DataResponse[Token]):
    """Registration response schema"""
    data: Token = Field(description="Authentication tokens")
    user: "UserResponse" = Field(description="Created user information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(description="Refresh token")


class RefreshTokenResponse(DataResponse[Token]):
    """Refresh token response schema"""
    data: Token = Field(description="New authentication tokens")


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=8, description="New password")
    confirm_password: str = Field(min_length=8, description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        """Validate that passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_number:
            raise ValueError('Password must contain at least one number')
        
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr = Field(description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(description="Password reset token")
    new_password: str = Field(min_length=8, description="New password")
    confirm_password: str = Field(min_length=8, description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        """Validate that passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_number:
            raise ValueError('Password must contain at least one number')
        
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""
    pass  # No additional fields needed, user is identified by token


class EmailVerificationConfirm(BaseModel):
    """Email verification confirmation schema"""
    token: str = Field(description="Email verification token")


class LogoutRequest(BaseModel):
    """Logout request schema"""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")
    logout_all_sessions: bool = Field(default=False, description="Whether to logout all sessions")


class ValidateSessionRequest(BaseModel):
    """Session validation request schema"""
    pass  # Access token is provided in Authorization header


class ValidateSessionResponse(BaseResponse):
    """Session validation response schema"""
    is_valid: bool = Field(description="Whether the session is valid")
    user: Optional["UserResponse"] = Field(None, description="User information if valid")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")


class SessionInfo(BaseModel):
    """Session information schema"""
    session_id: str = Field(description="Session identifier")
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="IP address")
    created_at: datetime = Field(description="Session creation time")
    last_seen_at: datetime = Field(description="Last activity time")
    is_current: bool = Field(description="Whether this is the current session")


class SessionListResponse(DataResponse[list[SessionInfo]]):
    """Session list response schema"""
    data: list[SessionInfo] = Field(description="List of user sessions")


class RevokeSessionRequest(BaseModel):
    """Revoke session request schema"""
    session_id: str = Field(description="Session ID to revoke")


class AccountDeletionRequest(BaseModel):
    """Account deletion request schema"""
    password: str = Field(description="Current password for confirmation")
    confirmation: str = Field(description="Type 'DELETE' to confirm")
    
    @validator('confirmation')
    def validate_confirmation(cls, v):
        """Validate deletion confirmation"""
        if v != 'DELETE':
            raise ValueError('Must type "DELETE" to confirm account deletion')
        return v


# OAuth schemas (for future implementation)
class OAuthProvider(BaseModel):
    """OAuth provider information"""
    provider: str = Field(description="OAuth provider name (google, github, etc.)")
    client_id: str = Field(description="OAuth client ID")
    authorize_url: str = Field(description="OAuth authorization URL")


class OAuthAuthorizationRequest(BaseModel):
    """OAuth authorization request"""
    provider: str = Field(description="OAuth provider name")
    redirect_uri: str = Field(description="Redirect URI after authorization")
    state: Optional[str] = Field(None, description="State parameter for security")


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request"""
    provider: str = Field(description="OAuth provider name")
    code: str = Field(description="Authorization code")
    state: Optional[str] = Field(None, description="State parameter")


class OAuthLoginResponse(DataResponse[Token]):
    """OAuth login response"""
    data: Token = Field(description="Authentication tokens")
    user: "UserResponse" = Field(description="User information")
    is_new_user: bool = Field(description="Whether this is a newly created user")


# Import UserResponse to resolve forward reference
from app.schemas.user import UserResponse

# Update forward references
LoginResponse.model_rebuild()
RegisterResponse.model_rebuild()
ValidateSessionResponse.model_rebuild()
OAuthLoginResponse.model_rebuild()