package main

import (
	"context"
	"crypto/rand"
	"crypto/subtle"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"html/template"
	"io"
	"log"
	"math/big"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sort"
	"strings"
	"sync"
	"syscall"
	"time"
)

const (
	host               = "127.0.0.1"
	defaultPort        = 8000
	defaultMaxAttempts = 40
	maxUsernameLength  = 64
	maxPasswordLength  = 128
	maxSourceLength    = 32
)

var (
	accountCandidates  = []string{"student01", "analyst", "operator"}
	passwordCandidates = []string{
		"Python#03",
		"Loop-2026",
		"Blue!234",
		"List&Dict7",
		"LocalOnly9",
		"Review_308",
	}
	errAttemptLimit = errors.New("attempt limit reached")
)

type authEvent struct {
	Sequence int    `json:"sequence"`
	Username string `json:"username"`
	Source   string `json:"source"`
	Result   string `json:"result"`
}

type labState struct {
	mu          sync.Mutex
	username    string
	password    string
	maxAttempts int
	events      []authEvent
}

func newLabState(username, password string, maxAttempts int) *labState {
	return &labState{
		username:    username,
		password:    password,
		maxAttempts: maxAttempts,
		events:      make([]authEvent, 0, maxAttempts),
	}
}

func (s *labState) authenticate(username, password, source string) (authEvent, int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if len(s.events) >= s.maxAttempts {
		return authEvent{}, 0, errAttemptLimit
	}

	result := "FAIL"
	userMatch := subtle.ConstantTimeCompare([]byte(username), []byte(s.username))
	passwordMatch := subtle.ConstantTimeCompare([]byte(password), []byte(s.password))
	if userMatch&passwordMatch == 1 {
		result = "SUCCESS"
	}

	event := authEvent{
		Sequence: len(s.events) + 1,
		Username: username,
		Source:   source,
		Result:   result,
	}
	s.events = append(s.events, event)
	return event, s.maxAttempts - len(s.events), nil
}

func (s *labState) snapshot() []authEvent {
	s.mu.Lock()
	defer s.mu.Unlock()

	result := make([]authEvent, len(s.events))
	copy(result, s.events)
	return result
}

func (s *labState) attemptCount() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.events)
}

type labApp struct {
	state     *labState
	blueToken string
}

func (a *labApp) handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/", a.handleRoot)
	mux.HandleFunc("/health", a.handleHealth)
	mux.HandleFunc("/login", a.handleLogin)
	mux.HandleFunc("/blue", a.handleBlue)
	mux.HandleFunc("/api/challenge", a.handleChallenge)
	mux.HandleFunc("/api/login", a.handleAPILogin)
	mux.HandleFunc("/api/events", a.handleAPIEvents)
	return securityHeaders(mux)
}

func securityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
		w.Header().Set("Referrer-Policy", "no-referrer")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		next.ServeHTTP(w, r)
	})
}

func requireGET(w http.ResponseWriter, r *http.Request) bool {
	if r.Method == http.MethodGet {
		return true
	}
	w.Header().Set("Allow", http.MethodGet)
	writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "GET 요청만 허용됩니다"})
	return false
}

func (a *labApp) handleRoot(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		writeJSON(w, http.StatusNotFound, map[string]string{"error": "not found"})
		return
	}
	if !requireGET(w, r) {
		return
	}
	http.Redirect(w, r, "/login", http.StatusFound)
}

func (a *labApp) handleHealth(w http.ResponseWriter, r *http.Request) {
	if !requireGET(w, r) {
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{
		"status":  "ok",
		"service": "python-basic-auth-lab",
		"scope":   "loopback-only",
	})
}

func (a *labApp) handleChallenge(w http.ResponseWriter, r *http.Request) {
	if !requireGET(w, r) {
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"accounts":      accountCandidates,
		"passwords":     passwordCandidates,
		"attempt_limit": a.state.maxAttempts,
		"target":        "provided localhost lab only",
	})
}

func validateAttemptInput(username, password, source string) error {
	if strings.TrimSpace(username) == "" || password == "" {
		return errors.New("계정명과 비밀번호를 모두 입력하세요")
	}
	if len(username) > maxUsernameLength {
		return fmt.Errorf("계정명은 %d자를 넘을 수 없습니다", maxUsernameLength)
	}
	if len(password) > maxPasswordLength {
		return fmt.Errorf("비밀번호는 %d자를 넘을 수 없습니다", maxPasswordLength)
	}
	if source == "" || len(source) > maxSourceLength {
		return fmt.Errorf("출발지 표시는 1~%d자여야 합니다", maxSourceLength)
	}
	for _, char := range source {
		if !((char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') ||
			(char >= '0' && char <= '9') || char == '-' || char == '_') {
			return errors.New("출발지 표시는 영문자, 숫자, -, _만 사용할 수 있습니다")
		}
	}
	return nil
}

func attemptValues(r *http.Request) (string, string, string) {
	query := r.URL.Query()
	username := query.Get("username")
	password := query.Get("password")
	source := query.Get("source")
	if source == "" {
		source = "red-lab-01"
	}
	return username, password, source
}

func (a *labApp) handleAPILogin(w http.ResponseWriter, r *http.Request) {
	if !requireGET(w, r) {
		return
	}
	username, password, source := attemptValues(r)
	if err := validateAttemptInput(username, password, source); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}

	event, remaining, err := a.state.authenticate(username, password, source)
	if errors.Is(err, errAttemptLimit) {
		writeJSON(w, http.StatusTooManyRequests, map[string]string{
			"error": "실습의 최대 인증 시도 횟수에 도달했습니다. 서버를 재시작해 초기화하세요",
		})
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"attempt":   event.Sequence,
		"remaining": remaining,
		"result":    event.Result,
		"username":  event.Username,
	})
}

type loginPageData struct {
	Accounts     []string
	Passwords    []string
	Username     string
	Source       string
	Message      string
	MessageClass string
	Attempts     int
	MaxAttempts  int
}

func (a *labApp) handleLogin(w http.ResponseWriter, r *http.Request) {
	if !requireGET(w, r) {
		return
	}

	username, password, source := attemptValues(r)
	data := loginPageData{
		Accounts:    accountCandidates,
		Passwords:   passwordCandidates,
		Username:    username,
		Source:      source,
		Attempts:    a.state.attemptCount(),
		MaxAttempts: a.state.maxAttempts,
	}

	query := r.URL.Query()
	if query.Has("username") || query.Has("password") {
		if err := validateAttemptInput(username, password, source); err != nil {
			data.Message = err.Error()
			data.MessageClass = "error"
		} else {
			event, _, err := a.state.authenticate(username, password, source)
			if errors.Is(err, errAttemptLimit) {
				data.Message = "최대 인증 시도 횟수에 도달했습니다. 서버를 재시작해 초기화하세요."
				data.MessageClass = "error"
			} else if event.Result == "SUCCESS" {
				data.Message = fmt.Sprintf("인증 성공: %s", event.Username)
				data.MessageClass = "success"
			} else {
				data.Message = "인증 실패: 계정명 또는 비밀번호를 확인하세요."
				data.MessageClass = "fail"
			}
			data.Attempts = a.state.attemptCount()
		}
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := loginTemplate.Execute(w, data); err != nil {
		log.Printf("login template error: %v", err)
	}
}

func (a *labApp) validBlueToken(value string) bool {
	if len(value) != len(a.blueToken) {
		return false
	}
	return subtle.ConstantTimeCompare([]byte(value), []byte(a.blueToken)) == 1
}

func (a *labApp) requestBlueToken(r *http.Request) string {
	if token := r.Header.Get("X-Blue-Token"); token != "" {
		return token
	}
	return r.URL.Query().Get("token")
}

func (a *labApp) handleAPIEvents(w http.ResponseWriter, r *http.Request) {
	if !requireGET(w, r) {
		return
	}
	if !a.validBlueToken(a.requestBlueToken(r)) {
		writeJSON(w, http.StatusForbidden, map[string]string{"error": "올바른 블루팀 토큰이 필요합니다"})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"events": a.state.snapshot()})
}

type bluePageData struct {
	Events []authEvent
}

func (a *labApp) handleBlue(w http.ResponseWriter, r *http.Request) {
	if !requireGET(w, r) {
		return
	}
	if !a.validBlueToken(a.requestBlueToken(r)) {
		writeJSON(w, http.StatusForbidden, map[string]string{"error": "콘솔에 출력된 블루팀 토큰이 필요합니다"})
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := blueTemplate.Execute(w, bluePageData{Events: a.state.snapshot()}); err != nil {
		log.Printf("blue template error: %v", err)
	}
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		log.Printf("json response error: %v", err)
	}
}

func randomChoice(values []string) (string, error) {
	index, err := rand.Int(rand.Reader, big.NewInt(int64(len(values))))
	if err != nil {
		return "", err
	}
	return values[index.Int64()], nil
}

func randomToken() (string, error) {
	raw := make([]byte, 16)
	if _, err := rand.Read(raw); err != nil {
		return "", err
	}
	return hex.EncodeToString(raw), nil
}

func shuffled(values []string) []string {
	result := append([]string(nil), values...)
	sort.Strings(result)
	return result
}

func run(port, maxAttempts int) error {
	username, err := randomChoice(accountCandidates)
	if err != nil {
		return fmt.Errorf("계정 선택 실패: %w", err)
	}
	password, err := randomChoice(passwordCandidates)
	if err != nil {
		return fmt.Errorf("비밀번호 선택 실패: %w", err)
	}
	blueToken, err := randomToken()
	if err != nil {
		return fmt.Errorf("블루팀 토큰 생성 실패: %w", err)
	}

	app := &labApp{
		state:     newLabState(username, password, maxAttempts),
		blueToken: blueToken,
	}
	address := fmt.Sprintf("%s:%d", host, port)
	listener, err := net.Listen("tcp", address)
	if err != nil {
		return fmt.Errorf("서버 시작 실패(%s): %w", address, err)
	}

	server := &http.Server{
		Handler:           app.handler(),
		ReadHeaderTimeout: 3 * time.Second,
		IdleTimeout:       30 * time.Second,
		ErrorLog:          log.New(io.Discard, "", 0),
	}

	fmt.Println("Python 03-9 로컬 인증 챌린지")
	fmt.Printf("로그인 페이지: http://%s/login\n", address)
	fmt.Printf("후보 계정: %s\n", strings.Join(shuffled(accountCandidates), ", "))
	fmt.Printf("후보 비밀번호: %s\n", strings.Join(shuffled(passwordCandidates), ", "))
	fmt.Printf("최대 인증 시도: %d회\n", maxAttempts)
	fmt.Printf("블루팀 이벤트: http://%s/blue?token=%s\n", address, blueToken)
	fmt.Println("실습을 끝내려면 Ctrl+C를 누르세요.")

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	serveError := make(chan error, 1)
	go func() {
		serveError <- server.Serve(listener)
	}()

	select {
	case <-ctx.Done():
		shutdownContext, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		return server.Shutdown(shutdownContext)
	case err := <-serveError:
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return err
	}
}

func main() {
	port := flag.Int("port", defaultPort, "로컬 서버 포트(1024~65535)")
	maxAttempts := flag.Int("max-attempts", defaultMaxAttempts, "최대 인증 시도(1~200)")
	flag.Parse()

	if *port < 1024 || *port > 65535 {
		log.Fatal("port는 1024~65535 범위여야 합니다")
	}
	if *maxAttempts < 1 || *maxAttempts > 200 {
		log.Fatal("max-attempts는 1~200 범위여야 합니다")
	}
	if err := run(*port, *maxAttempts); err != nil {
		log.Fatal(err)
	}
}

var loginTemplate = template.Must(template.New("login").Parse(`<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Python 03-9 인증 챌린지</title>
  <style>
    :root { color-scheme: light; font-family: system-ui, sans-serif; }
    body { max-width: 900px; margin: 3rem auto; padding: 0 1rem; background: #f4f7fb; color: #162033; }
    main { background: white; border: 1px solid #dbe3ef; border-radius: 16px; padding: 2rem; box-shadow: 0 12px 30px #18315314; }
    h1 { margin-top: 0; }
    .warning { border-left: 5px solid #e49b0f; background: #fff7df; padding: 1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
    .card { border: 1px solid #dbe3ef; border-radius: 12px; padding: 1rem; }
    label { display: block; margin-top: 1rem; font-weight: 700; }
    input { width: 100%; box-sizing: border-box; margin-top: .4rem; padding: .75rem; border: 1px solid #aab7c8; border-radius: 8px; }
    button { margin-top: 1.25rem; border: 0; border-radius: 8px; padding: .8rem 1.25rem; background: #155eef; color: white; font-weight: 700; cursor: pointer; }
    .message { margin: 1.25rem 0; padding: 1rem; border-radius: 8px; font-weight: 700; }
    .success { background: #e8f7ee; color: #17633a; }
    .fail, .error { background: #fff0f0; color: #9b1c1c; }
    code { background: #eef2f7; padding: .15rem .35rem; border-radius: 4px; }
    li { margin: .35rem 0; }
  </style>
</head>
<body>
<main>
  <h1>Python 03-9 인증 챌린지</h1>
  <p>정답 조합은 서버를 실행할 때 무작위로 정해집니다. 제공된 로컬 환경에서만 실습하세요.</p>
  <div class="warning"><strong>의도적으로 GET을 사용하는 학습 페이지입니다.</strong> 입력값이 URL에 나타나는 이유를 관찰하고, 실제 인증에는 POST와 HTTPS가 필요함을 설명하세요.</div>

  <div class="grid">
    <section class="card">
      <h2>후보 계정</h2>
      <ul>{{range .Accounts}}<li><code>{{.}}</code></li>{{end}}</ul>
    </section>
    <section class="card">
      <h2>후보 비밀번호</h2>
      <ul>{{range .Passwords}}<li><code>{{.}}</code></li>{{end}}</ul>
    </section>
  </div>

  {{if .Message}}<div class="message {{.MessageClass}}">{{.Message}}</div>{{end}}

  <form action="/login" method="get" autocomplete="off">
    <label for="username">계정명</label>
    <input id="username" name="username" value="{{.Username}}" maxlength="64" required>

    <label for="password">비밀번호</label>
    <input id="password" name="password" type="password" maxlength="128" required>

    <label for="source">실습 출발지 표시</label>
    <input id="source" name="source" value="{{.Source}}" maxlength="32" pattern="[A-Za-z0-9_-]+" required>

    <button type="submit">인증 시도</button>
  </form>
  <p>현재 시도: <strong>{{.Attempts}}</strong> / {{.MaxAttempts}}</p>
  <p>Python 프로그램에서는 <code>/api/challenge</code>와 <code>/api/login</code>을 사용합니다.</p>
</main>
</body>
</html>`))

var blueTemplate = template.Must(template.New("blue").Parse(`<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>블루팀 인증 이벤트</title>
  <style>
    :root { font-family: system-ui, sans-serif; }
    body { max-width: 960px; margin: 3rem auto; padding: 0 1rem; color: #172033; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #dbe3ef; padding: .7rem; text-align: left; }
    th { background: #eef4ff; }
    code { background: #eef2f7; padding: .15rem .35rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>블루팀 인증 이벤트</h1>
  <p>비밀번호 원문은 기록되지 않습니다. 아래 원시 이벤트를 Python으로 집계하세요.</p>
  <table>
    <thead><tr><th>순서</th><th>계정</th><th>출발지</th><th>결과</th></tr></thead>
    <tbody>
      {{range .Events}}<tr><td>{{.Sequence}}</td><td><code>{{.Username}}</code></td><td>{{.Source}}</td><td>{{.Result}}</td></tr>{{else}}<tr><td colspan="4">아직 인증 이벤트가 없습니다.</td></tr>{{end}}
    </tbody>
  </table>
</body>
</html>`))
