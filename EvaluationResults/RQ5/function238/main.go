package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

var googleMapsAPIKey = os.Getenv("GOOGLE_MAPS_API_KEY")

func handler(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	switch request.Path {
	case "/geolocation":
		return handleGeolocation(request)
	case "/nearbylocation":
		return handleNearbyLocation(request)
	case "/geodetail":
		return handleGeoDetail(request)
	default:
		return events.APIGatewayProxyResponse{StatusCode: http.StatusNotFound}, nil
	}
}

func handleGeolocation(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	address := request.QueryStringParameters["address"]
	if address == "" {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusBadRequest, Body: "Address parameter is required"}, nil
	}

	url := fmt.Sprintf("https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s", address, googleMapsAPIKey)
	resp, err := http.Get(url)
	if err != nil {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusInternalServerError, Body: err.Error()}, nil
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusInternalServerError, Body: err.Error()}, nil
	}

	return events.APIGatewayProxyResponse{StatusCode: http.StatusOK, Body: string(body)}, nil
}

func handleNearbyLocation(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	location := request.QueryStringParameters["location"]
	radius := request.QueryStringParameters["radius"]
	name := request.QueryStringParameters["name"]

	if location == "" || radius == "" {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusBadRequest, Body: "Location and radius parameters are required"}, nil
	}

	url := fmt.Sprintf("https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=%s&radius=%s&key=%s", location, radius, googleMapsAPIKey)
	if name != "" {
		url += fmt.Sprintf("&name=%s", name)
	}

	resp, err := http.Get(url)
	if err != nil {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusInternalServerError, Body: err.Error()}, nil
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusInternalServerError, Body: err.Error()}, nil
	}

	return events.APIGatewayProxyResponse{StatusCode: http.StatusOK, Body: string(body)}, nil
}

func handleGeoDetail(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	placeID := request.QueryStringParameters["placeid"]
	if placeID == "" {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusBadRequest, Body: "Place ID parameter is required"}, nil
	}

	url := fmt.Sprintf("https://maps.googleapis.com/maps/api/place/details/json?placeid=%s&key=%s", placeID, googleMapsAPIKey)
	resp, err := http.Get(url)
	if err != nil {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusInternalServerError, Body: err.Error()}, nil
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return events.APIGatewayProxyResponse{StatusCode: http.StatusInternalServerError, Body: err.Error()}, nil
	}

	return events.APIGatewayProxyResponse{StatusCode: http.StatusOK, Body: string(body)}, nil
}

func main() {
	lambda.Start(handler)
}