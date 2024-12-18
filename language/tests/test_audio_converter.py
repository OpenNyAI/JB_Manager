from io import BytesIO
from unittest.mock import AsyncMock, patch, MagicMock
from urllib.parse import ParseResult
import pytest
from src.audio_converter import _get_file_extension, _is_url, convert_to_wav, convert_to_wav_with_ffmpeg, convert_wav_bytes_to_mp3_bytes, get_filename_from_url

@pytest.mark.parametrize(
        "mock_string, parsed_url_string", 
        [("http://test.com/media/test_audio_file.mp3", 
          ParseResult(scheme='http', netloc='test.com', path='/media/test_audio_file.mp3', params='', query='', fragment='')),
        ]
)
def test_is_url_with_valid_url(mock_string, parsed_url_string):
    with patch("src.audio_converter.urlparse", return_value=parsed_url_string) as mock_url_parse:
        result = _is_url(mock_string)
        assert result == True

        mock_url_parse.assert_called_once_with(mock_string)

@pytest.mark.parametrize(
        "mock_string, parsed_url_string", 
        [("/media/test_audio_file.mp3", 
          ParseResult(scheme='', netloc='', path='/media/test_audio_file.mp3', params='', query='', fragment='')),
        ]
)
def test_is_url_with_invalid_url(mock_string, parsed_url_string):
    with patch("src.audio_converter.urlparse", return_value=parsed_url_string) as mock_url_parse:

        result = _is_url(mock_string)

        assert result == False
        mock_url_parse.assert_called_once_with(mock_string)

@pytest.mark.parametrize("mock_string", [("invalid string")])
def test_is_url_failure(mock_string):
    with patch("src.audio_converter.urlparse", side_effect = ValueError) as mock_url_parse:

        result = _is_url(mock_string)

        assert result == False
        mock_url_parse.assert_called_once_with(mock_string)

@pytest.mark.parametrize(
        "mock_url, parsed_url", 
        [("http://test.com/media/test_audio_file.mp3", 
          ParseResult(scheme='http', netloc='test.com', path='/media/test_audio_file.mp3', params='', query='', fragment='')),
        ]
)
def test_get_filename_from_url(mock_url, parsed_url):
    with patch("src.audio_converter.urlparse", return_value=parsed_url) as mock_url_parse:

        result = get_filename_from_url(mock_url)

        assert result == "test_audio_file.mp3"
        mock_url_parse.assert_called_once_with(mock_url)

@pytest.mark.parametrize("mock_file_name_or_url", [("http://test.com/media/test_audio_file.mp3")])
def test_get_file_extension_when_file_name_or_url_starts_with_http_or_https(mock_file_name_or_url):

    file_name = "test_audio_file.mp3"

    with patch("src.audio_converter.get_filename_from_url", return_value=file_name) as mock_get_filename_from_url:

        result = _get_file_extension(mock_file_name_or_url)

        assert result == "mp3"
        mock_get_filename_from_url.assert_called_once_with(mock_file_name_or_url)

@pytest.mark.parametrize("mock_file_name_or_url", [("/media/test_audio_file.mp3")])
def test_get_file_extension_when_file_name_or_url_does_not_start_with_http_or_https(mock_file_name_or_url):

    result = _get_file_extension(mock_file_name_or_url)

    assert result == "mp3"

@pytest.mark.parametrize("mock_source_url_or_file", [("http://test.com/media/test_audio_file.mp3")])
def test_convert_to_wav_with_url(mock_source_url_or_file):
    
    with patch('src.audio_converter._get_file_extension') as mock_get_file_extension, \
      patch('src.audio_converter._is_url') as mock_is_url, \
        patch('src.audio_converter.httpx.get') as mock_httpx_get, \
          patch('pydub.AudioSegment.from_file') as mock_audio_segment:
        
        mock_get_file_extension.return_value = 'mp3'
        mock_is_url.return_value = True

        mock_response = MagicMock()
        mock_response.content = b"test audio content"
        mock_httpx_get.return_value = mock_response
        
        mock_audio = MagicMock()
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.export.return_value = None
        mock_audio_segment.return_value = mock_audio

        result_wav_data = convert_to_wav(mock_source_url_or_file)
        
        assert isinstance(result_wav_data, bytes)
        
        mock_get_file_extension.assert_called_once_with(mock_source_url_or_file)
        mock_is_url.assert_called_once_with(mock_source_url_or_file)
        mock_httpx_get.assert_called_once_with(mock_source_url_or_file)
        mock_audio_segment.assert_called_once()

@pytest.mark.parametrize("mock_source_url_or_file", [("/media/test_audio_file.mp3")])
def test_convert_to_wav_with_local_file(mock_source_url_or_file):
    
    with patch('src.audio_converter._get_file_extension') as mock_get_file_extension, \
      patch('src.audio_converter._is_url') as mock_is_url, patch('pydub.AudioSegment.from_file') as mock_audio_segment:
      
      mock_get_file_extension.return_value = 'mp3'
      mock_is_url.return_value = False
      
      mock_audio = MagicMock()
      mock_audio.set_frame_rate.return_value = mock_audio
      mock_audio.set_channels.return_value = mock_audio
      mock_audio.export.return_value = None
      mock_audio_segment.return_value = mock_audio

      result_wav_data = convert_to_wav(mock_source_url_or_file)

      assert isinstance(result_wav_data, bytes)

      mock_get_file_extension.assert_called_once_with(mock_source_url_or_file)
      mock_is_url.assert_called_once_with(mock_source_url_or_file)
      mock_audio_segment.assert_called_once_with(mock_source_url_or_file, format="mp3")

@pytest.mark.parametrize("mock_wav_bytes", [(b"some wav content")])
def test_convert_wav_bytes_to_mp3_bytes(mock_wav_bytes):
    
    mock_wav_file = BytesIO(mock_wav_bytes)
    
    with patch('src.audio_converter.BytesIO', return_value = mock_wav_file) as mock_bytes_io, \
      patch('pydub.AudioSegment.from_file') as mock_audio_segment:
      
      mock_audio = MagicMock()
      mock_audio.set_frame_rate.return_value = mock_audio
      mock_audio.export.return_value = None
      mock_audio_segment.return_value = mock_audio

      result = convert_wav_bytes_to_mp3_bytes(mock_wav_bytes)

      assert isinstance(result, bytes)
      assert mock_bytes_io.call_count == 2
      
      mock_bytes_io.assert_any_call(mock_wav_bytes)
      mock_bytes_io.assert_called_with()
      mock_audio_segment.assert_called_once_with(mock_wav_file, format="wav")

@pytest.mark.asyncio
@pytest.mark.parametrize("mock_source_url_or_file", [("http://test.com/media/test_audio_file.mp3")])
async def test_convert_to_wav_with_ffmpeg_for_valid_url(mock_source_url_or_file):
    
    with patch('src.audio_converter._get_file_extension', return_value = "mp3") as mock_get_file_extension, \
      patch('src.audio_converter._is_url', return_value = True) as mock_is_url, \
        patch('src.audio_converter.httpx.get') as mock_httpx_get, \
          patch('src.audio_converter.subprocess.run') as mock_subprocess_run, \
            patch('src.audio_converter.aiofiles.open') as mock_aiofiles_open, \
              patch('src.audio_converter.aiofiles.os.remove', return_value = None) as mock_aiofiles_os_remove:

        mock_response = MagicMock()
        mock_response.content = b"test audio content"
        mock_httpx_get.return_value = mock_response

        mock_subprocess_run.return_value = None

        mock_wav_file = AsyncMock()
        mock_wav_file.read.return_value = b"test audio data"
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_wav_file

        result_audio_data = await convert_to_wav_with_ffmpeg(mock_source_url_or_file)
        
        assert isinstance(result_audio_data, bytes)
        
        mock_get_file_extension.assert_called_once_with(mock_source_url_or_file)
        mock_is_url.assert_called_once_with(mock_source_url_or_file)
        mock_httpx_get.assert_called_once_with(mock_source_url_or_file)
        mock_subprocess_run.assert_called_once()
        mock_aiofiles_open.assert_called_once()
        mock_aiofiles_os_remove.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.parametrize("mock_source_url_or_file", [("/media/test_audio_file.mp3")])
async def test_convert_to_wav_with_ffmpeg_for_local_file(mock_source_url_or_file):
    
    with patch('src.audio_converter._get_file_extension', return_value = "mp3") as mock_get_file_extension, \
      patch('src.audio_converter._is_url', return_value = False) as mock_is_url, \
        patch('src.audio_converter.subprocess.run') as mock_subprocess_run, \
          patch('src.audio_converter.aiofiles.open') as mock_aiofiles_open, \
            patch('src.audio_converter.aiofiles.os.remove', return_value = None) as mock_aiofiles_os_remove:

        mock_subprocess_run.return_value = None

        mock_wav_file = AsyncMock()
        mock_wav_file.read.return_value = b"test audio data"
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_wav_file

        result_audio_data = await convert_to_wav_with_ffmpeg(mock_source_url_or_file)
        
        assert isinstance(result_audio_data, bytes)
        
        mock_get_file_extension.assert_called_once_with(mock_source_url_or_file)
        mock_is_url.assert_called_once_with(mock_source_url_or_file)
        mock_subprocess_run.assert_called_once()
        mock_aiofiles_open.assert_called_once()
        mock_aiofiles_os_remove.assert_awaited_once()
