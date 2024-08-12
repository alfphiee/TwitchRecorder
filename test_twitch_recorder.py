import pytest
import os
import re
import json
from twitch_recorder import load_config, is_streamer_live, download_stream
from unittest.mock import patch


def test_load_config(tmp_path):
  # Test Loading of Config File
    config_data = {
        "channels": ["test_channel1", "test_channel2"],
        "check_interval": 60,
        "output_directory": "/path/to/output"
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))
    
    config = load_config(config_file)
    
    assert config["channels"] == ["test_channel1", "test_channel2"]
    assert config["check_interval"] == 60
    assert config["output_directory"] == "/path/to/output"

@patch('twitch_recorder.requests.get')
def test_is_streamer_live(mock_get):
    # Mock a response where the streamer is live
    mock_get.return_value.content = b'isLiveBroadcast'
    is_live, stream_title = is_streamer_live('test_channel')
    
    assert is_live is True
    assert stream_title is None  # Modify based on how stream_title is extracted

@patch('twitch_recorder.requests.get')
def test_is_streamer_not_live(mock_get):
    # Mock a response where the streamer is not live
    mock_get.return_value.content = b'some other content'
    is_live, stream_title = is_streamer_live('test_channel')
    
    assert is_live is False
    assert stream_title is None

@patch('twitch_recorder.subprocess.Popen')
def test_download_stream(mock_popen):
    mock_process = mock_popen.return_value
    mock_process.communicate.return_value = (b'', b'')  # Mock no output or errors
    
    channel_name = "test_channel"
    stream_title = "test_stream"
    output_dir = "/path/to/output"
    
    # Run the function
    process = download_stream(channel_name, stream_title, output_dir)
    
    # Get the actual call arguments
    actual_calls = [call[0][0] for call in mock_popen.call_args_list]
    
    # Define the expected partial command pattern (ignoring the timestamp)
    expected_command_pattern = re.compile(
        r"streamlink --twitch-disable-ads twitch.tv/test_channel best -o /path/to/output\\test_channel\\test_stream_\d{8}_\d{6}.mp4"
    )

    # Check that the first command matches the expected pattern
    assert any(expected_command_pattern.match(" ".join(call)) for call in actual_calls)
    
    # Ensure Popen was called the expected number of times (2 in this case)
    assert mock_popen.call_count == 2