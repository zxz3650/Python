package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

func testServer(maxAttempts int) (*httptest.Server, string) {
	token := "blue-test-token"
	app := &labApp{
		state:     newLabState("student01", "Blue!234", maxAttempts),
		blueToken: token,
	}
	return httptest.NewServer(app.handler()), token
}

func TestLoginPageOpens(t *testing.T) {
	server, _ := testServer(3)
	defer server.Close()

	response, err := http.Get(server.URL + "/login")
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want %d", response.StatusCode, http.StatusOK)
	}
	body, _ := io.ReadAll(response.Body)
	if !strings.Contains(string(body), "Python 03-9 인증 챌린지") {
		t.Fatal("login page title is missing")
	}
}

func TestAuthenticationAndEventsDoNotExposePassword(t *testing.T) {
	server, token := testServer(3)
	defer server.Close()

	for _, attempt := range []struct {
		password string
		want     string
	}{
		{password: "wrong-password", want: "FAIL"},
		{password: "Blue!234", want: "SUCCESS"},
	} {
		endpoint := server.URL + "/api/login?" + url.Values{
			"username": {"student01"},
			"password": {attempt.password},
			"source":   {"red-lab-01"},
		}.Encode()
		response, err := http.Get(endpoint)
		if err != nil {
			t.Fatal(err)
		}
		var payload map[string]any
		if err := json.NewDecoder(response.Body).Decode(&payload); err != nil {
			response.Body.Close()
			t.Fatal(err)
		}
		response.Body.Close()
		if payload["result"] != attempt.want {
			t.Fatalf("result = %v, want %s", payload["result"], attempt.want)
		}
	}

	request, _ := http.NewRequest(http.MethodGet, server.URL+"/api/events", nil)
	request.Header.Set("X-Blue-Token", token)
	response, err := http.DefaultClient.Do(request)
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	body, _ := io.ReadAll(response.Body)
	text := string(body)
	if strings.Contains(text, "wrong-password") || strings.Contains(text, "Blue!234") {
		t.Fatalf("event response exposed a password: %s", text)
	}
	if !strings.Contains(text, `"result":"SUCCESS"`) {
		t.Fatalf("success event is missing: %s", text)
	}
}

func TestAttemptLimit(t *testing.T) {
	server, _ := testServer(1)
	defer server.Close()

	endpoint := server.URL + "/api/login?username=student01&password=wrong&source=red-lab-01"
	first, err := http.Get(endpoint)
	if err != nil {
		t.Fatal(err)
	}
	first.Body.Close()

	second, err := http.Get(endpoint)
	if err != nil {
		t.Fatal(err)
	}
	defer second.Body.Close()
	if second.StatusCode != http.StatusTooManyRequests {
		t.Fatalf("status = %d, want %d", second.StatusCode, http.StatusTooManyRequests)
	}
}

func TestBlueEventsRequireToken(t *testing.T) {
	server, _ := testServer(3)
	defer server.Close()

	response, err := http.Get(server.URL + "/api/events")
	if err != nil {
		t.Fatal(err)
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusForbidden {
		t.Fatalf("status = %d, want %d", response.StatusCode, http.StatusForbidden)
	}
}
