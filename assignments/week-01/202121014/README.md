문제 1 : Node.js 버전 차이



실습에서는 Node.js 20 LTS 설치를 권장했지만, 실제로 설치된 버전은 Node.js 24였다.



확인 명령어: node -v

출력 결과 : v24.14.0



해결방법 : Node.js 24에서도 Codex CLI가 정상적으로 작동하는 것을 확인하고 그대로 진행하였다.



문제 2 : Codex CLI 인증 방식 선택



Codex CLI 실행 시 로그인 방식을 선택해야 하는 단계가 있었다.



선택 옵션:

1\. Sign in with ChatGPT

2\. Sign in with Device Code

3\. Provide your own API key



API 키를 사용하는 방법도 있었지만, ChatGPT 계정 로그인 방식을 선택하였다.



해결 방법: ChatGPT 계정으로 로그인하여 별도의 API 키 없이 Codex CLI를 사용할 수 있었다.



->  이 과정을 통해 Codex CLI를 정상적으로 실행하고 Python 파일을 생성할 수 있었다.





