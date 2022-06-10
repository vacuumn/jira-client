from enum import Enum


class JiraEnvironment(Enum):
    Dev = 'https://jirarest-dev.example.com'
    Staging = 'https://jirarest-stage.example.com'
    Prod = 'https://jirarest.example.com'
