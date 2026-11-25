from pydantic import BaseModel,Field
class LoginInput(BaseModel):
    username:str=Field(min_length=1,max_length=80)
    password:str=Field(min_length=1,max_length=256)
class CaseInput(BaseModel):
    title:str=Field(min_length=3,max_length=180)
    scope:str=Field(min_length=15,max_length=3000)
