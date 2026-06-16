```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"net/http"
)

type Response struct {
	Message string `json:"message"`
}

func handler(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	switch request.HTTPMethod {
	case http.MethodGet:
		if name, ok := request.PathParameters["name"]; ok {
			// GET endpoint with name parameter
			return events.APIGatewayProxyResponse{
				StatusCode: http.StatusOK,
				Body:       fmt.Sprintf(`{"message": "Hello, %s!"}`, name),
			}, nil
		} else if name, ok := request.QueryStringParameters["name"]; ok {
			// GET endpoint with query string parameter
			return events.APIGatewayProxyResponse{
				StatusCode: http.StatusOK,
				Body:       fmt.Sprintf(`{"message": "Hello, %s!"}`, name),
			}, nil
		}
	case http.MethodPost:
		// POST endpoint with name in the body
		var requestBody map[string]string
		if err := json.Unmarshal([]byte(request.Body), &requestBody); err != nil {
			return events.APIGatewayProxyResponse{
				StatusCode: http.StatusBadRequest,
				Body:       `{"message": "Invalid request body"}`,
			}, nil
		}
		if name, ok := requestBody["name"]; ok {
			return events.APIGatewayProxyResponse{
				StatusCode: http.StatusOK,
				Body:       fmt.Sprintf(`{"message": "Hello, %s!"}`, name),
			}, nil
		}
	}

	return events.APIGatewayProxyResponse{
		StatusCode: http.StatusBadRequest,
		Body:       `{"message": "Invalid request"}`,
	}, nil
}

func main() {
	lambda.Start(handler)
}
```