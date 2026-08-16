from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    number: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=128)
    email: str = Field(min_length=3, max_length=254)
    nickname: str | None = Field(default=None, max_length=48)


class LoginRequest(BaseModel):
    number: str
    password: str


class AccountUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=48)
    current_password: str | None = Field(default=None, max_length=128)
    new_password: str | None = Field(default=None, min_length=6, max_length=128)


class FriendRequestCreate(BaseModel):
    receiver: str


class FriendProfileUpdate(BaseModel):
    alias: str | None = Field(default=None, max_length=48)
    tags: list[str] | None = Field(default=None, max_length=12)


class GroupCreate(BaseModel):
    title: str = Field(default="", max_length=80)
    members: list[str] = Field(default_factory=list, max_length=50)


class GroupInviteCreate(BaseModel):
    invitees: list[str] = Field(min_length=1, max_length=50)


class GroupUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=80)


class GroupAliasUpdate(BaseModel):
    alias: str = Field(default="", max_length=48)


class MessageCreate(BaseModel):
    receiver: str | None = None
    message_type: str = Field(default="text")
    body: str = Field(min_length=1, max_length=4000)
