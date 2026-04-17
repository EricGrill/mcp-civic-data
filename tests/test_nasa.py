"""Tests for NASA API tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.nasa import (
    get_astronomy_photo,
    get_mars_rover_photos,
    query_nasa,
    search_nasa_images,
)


class TestGetAstronomyPhoto(unittest.IsolatedAsyncioTestCase):
    """Tests for get_astronomy_photo tool."""

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_successful_apod(self, mock_fetch):
        mock_fetch.return_value = {
            "title": "The Eagle Nebula",
            "date": "2024-06-15",
            "explanation": "A stunning view of the Eagle Nebula.",
            "media_type": "image",
            "url": "https://apod.nasa.gov/apod/image/eagle.jpg",
        }
        result = await get_astronomy_photo(date="2024-06-15")
        self.assertIn("Eagle Nebula", result)
        self.assertIn("2024-06-15", result)
        self.assertIn("Image", result)

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_apod_video(self, mock_fetch):
        mock_fetch.return_value = {
            "title": "A Space Video",
            "date": "2024-06-16",
            "explanation": "An amazing video.",
            "media_type": "video",
            "url": "https://youtube.com/watch?v=test",
        }
        result = await get_astronomy_photo()
        self.assertIn("Video", result)

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_apod_network_error(self, mock_fetch):
        mock_fetch.side_effect = RuntimeError("API rate limit exceeded")
        with self.assertRaises(RuntimeError):
            await get_astronomy_photo()


class TestGetMarsRoverPhotos(unittest.IsolatedAsyncioTestCase):
    """Tests for get_mars_rover_photos tool."""

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_successful_photos(self, mock_fetch):
        mock_fetch.return_value = {
            "photos": [
                {
                    "camera": {"full_name": "Front Hazard Avoidance Camera"},
                    "sol": 1000,
                    "earth_date": "2015-05-30",
                    "img_src": "https://mars.nasa.gov/photo1.jpg",
                },
                {
                    "camera": {"full_name": "Rear Hazard Avoidance Camera"},
                    "sol": 1000,
                    "earth_date": "2015-05-30",
                    "img_src": "https://mars.nasa.gov/photo2.jpg",
                },
            ]
        }
        result = await get_mars_rover_photos(rover="curiosity", sol=1000)
        self.assertIn("Curiosity", result)
        self.assertIn("Front Hazard", result)
        self.assertIn("2 photos", result)

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_no_photos(self, mock_fetch):
        mock_fetch.return_value = {"photos": []}
        result = await get_mars_rover_photos(rover="spirit", sol=999999)
        self.assertIn("No photos found", result)

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_photos_limited_to_10(self, mock_fetch):
        photos = [
            {
                "camera": {"full_name": f"Camera {i}"},
                "sol": 100,
                "earth_date": "2020-01-01",
                "img_src": f"https://mars.nasa.gov/photo{i}.jpg",
            }
            for i in range(15)
        ]
        mock_fetch.return_value = {"photos": photos}
        result = await get_mars_rover_photos(rover="curiosity", sol=100)
        self.assertIn("Camera 9", result)
        self.assertNotIn("Camera 10", result)

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_default_sol(self, mock_fetch):
        mock_fetch.return_value = {"photos": []}
        await get_mars_rover_photos(rover="curiosity")
        call_args = mock_fetch.call_args
        params = call_args[1].get("params", call_args[0][1] if len(call_args[0]) > 1 else {})
        self.assertEqual(params.get("sol"), 1000)


class TestSearchNasaImages(unittest.IsolatedAsyncioTestCase):
    """Tests for search_nasa_images tool."""

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_successful_search(self, mock_fetch):
        mock_fetch.return_value = {
            "collection": {
                "items": [
                    {
                        "data": [
                            {
                                "title": "Apollo 11 Launch",
                                "date_created": "1969-07-16T00:00:00Z",
                                "description": "The launch of Apollo 11 mission.",
                            }
                        ],
                        "links": [{"href": "https://images.nasa.gov/thumb1.jpg"}],
                    }
                ]
            }
        }
        result = await search_nasa_images(query="apollo 11")
        self.assertIn("Apollo 11 Launch", result)
        self.assertIn("1969-07-16", result)

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_no_results(self, mock_fetch):
        mock_fetch.return_value = {"collection": {"items": []}}
        result = await search_nasa_images(query="xyznonexistent")
        self.assertIn("No results found", result)

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_search_with_no_links(self, mock_fetch):
        mock_fetch.return_value = {
            "collection": {
                "items": [
                    {
                        "data": [{"title": "Test Image", "date_created": "2020-01-01", "description": "Test"}],
                        "links": [],
                    }
                ]
            }
        }
        result = await search_nasa_images(query="test")
        self.assertIn("Test Image", result)
        self.assertIn("N/A", result)


class TestQueryNasa(unittest.IsolatedAsyncioTestCase):
    """Tests for query_nasa tool."""

    @patch("mcp_govt_api.tools.nasa.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = {"title": "Test APOD"}
        result = await query_nasa("/planetary/apod", params={"date": "2024-01-01"})
        self.assertEqual(result["title"], "Test APOD")
        # Verify api_key was injected
        call_params = mock_fetch.call_args[1].get("params", mock_fetch.call_args[0][1] if len(mock_fetch.call_args[0]) > 1 else {})
        self.assertIn("api_key", call_params)


if __name__ == "__main__":
    unittest.main()
