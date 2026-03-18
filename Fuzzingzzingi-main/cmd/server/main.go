package main

import (
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"github.com/gin-gonic/gin"

	"fuzzingzzingi/internal/crawler"
)

type crawlStatus struct {
	sync.Mutex
	Running     bool   `json:"running"`
	LastCommand string `json:"last_command,omitempty"`
	LastError   string `json:"last_error,omitempty"`
	OutputFile  string `json:"output_file,omitempty"`
}

var status = &crawlStatus{
	Running:    false,
	OutputFile: "output.txt",
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	router := gin.Default()

	router.POST("/api/crawl", handleCrawl)
	router.GET("/api/status", handleStatus)

	// 정적 파일(UI 빌드 결과) 서빙
	uiDir := filepath.Join(".", "ui", "dist")
	router.Static("/assets", filepath.Join(uiDir, "assets"))
	router.NoRoute(func(c *gin.Context) {
		if strings.HasPrefix(c.Request.URL.Path, "/api") {
			c.JSON(http.StatusNotFound, gin.H{"ok": false, "error": "not found"})
			return
		}
		indexPath := filepath.Join(uiDir, "index.html")
		if _, err := os.Stat(indexPath); err == nil {
			c.File(indexPath)
			return
		}
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"ok":      false,
			"message": "UI 빌드 결과가 없습니다. ui 디렉터리에서 `npm run build` 후 다시 시도하세요.",
		})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}
	if err := router.Run("0.0.0.0:" + port); err != nil {
		log.Fatalf("서버 실행 실패: %v", err)
	}
}

func handleCrawl(c *gin.Context) {
	var req crawler.Request
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"ok": false, "error": "잘못된 요청입니다"})
		return
	}
	if req.StartURL == "" {
		c.JSON(http.StatusBadRequest, gin.H{"ok": false, "error": "startUrl이 필요합니다"})
		return
	}
	if req.MaxDepth == 0 {
		req.MaxDepth = 3
	}
	if req.ProxyURL == "" {
		req.ProxyURL = "none"
	}

	status.Lock()
	defer status.Unlock()
	if status.Running {
		c.JSON(http.StatusConflict, gin.H{"ok": false, "error": "크롤러가 이미 실행 중입니다"})
		return
	}
	status.Running = true
	status.LastCommand = req.String()
	status.LastError = ""

	go func() {
		err := crawler.Run(req)
		status.Lock()
		defer status.Unlock()
		if err != nil {
			status.LastError = err.Error()
		}
		status.Running = false
	}()

	c.JSON(http.StatusOK, gin.H{"ok": true, "message": "크롤링을 시작했습니다", "command": req.String()})
}

func handleStatus(c *gin.Context) {
	status.Lock()
	defer status.Unlock()
	c.JSON(http.StatusOK, gin.H{
		"running":      status.Running,
		"last_command": status.LastCommand,
		"last_error":   status.LastError,
		"output_file":  status.OutputFile,
	})
}
