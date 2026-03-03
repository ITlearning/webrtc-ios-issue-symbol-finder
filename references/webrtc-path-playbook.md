# WebRTC Path Playbook

Use this map when ranking hypotheses and blast radius.

## Core Search Roots

- `sdk/objc/`: Obj-C surface + iOS bridge layer.
- `pc/`: PeerConnection C++ logic.
- `api/`: Public interfaces and API contracts.
- `p2p/base/`: ICE, STUN/TURN, transport internals.
- `media/engine/`: Media engine and codec pipeline.

## Symptom to Hotspot Mapping

### Audio interruptions, route changes, CallKit activation

- Primary files:
  - `sdk/objc/components/audio/RTCAudioSession.mm`
  - `sdk/objc/components/audio/RTCAudioSession.h`
  - `sdk/objc/native/src/audio/audio_device_ios.mm`
  - `sdk/objc/native/src/audio/voice_processing_audio_unit.mm`
- Symbols:
  - `RTCAudioSession`
  - `audioSessionDidActivate`
  - `audioSessionDidDeactivate`
  - `AVAudioSessionRouteChangeReason`
  - `setCategory`
  - `setActive`

### Camera capture start/stop/freeze/orientation

- Primary files:
  - `sdk/objc/components/capturer/RTCCameraVideoCapturer.m`
  - `sdk/objc/helpers/RTCDispatcher.m`
  - `sdk/objc/helpers/AVCaptureSession+DevicePosition.mm`
- Symbols:
  - `RTCCameraVideoCapturer`
  - `RTCDispatcherTypeCaptureSession`
  - `AVCaptureSession`

### Black frame or renderer view issues

- Primary files:
  - `sdk/objc/components/renderer/metal/RTCMTLVideoView.m`
  - `sdk/objc/components/renderer/opengl/RTCEAGLVideoView.m`
  - `sdk/objc/components/video_frame_buffer/RTCCVPixelBuffer.mm`
- Symbols:
  - `RTCMTLVideoView`
  - `RTCEAGLVideoView`
  - `RTCCVPixelBuffer`

### ICE disconnect/reconnect/state mismatch

- Primary files:
  - `sdk/objc/api/peerconnection/RTCPeerConnection.mm`
  - `sdk/objc/api/peerconnection/RTCPeerConnection+Private.h`
  - `pc/peer_connection.cc`
  - `pc/jsep_transport_controller.cc`
  - `p2p/base/p2p_transport_channel.cc`
- Symbols:
  - `OnIceConnectionChange`
  - `didChangeIceConnectionState`
  - `RTCIceCandidate`
  - `RTCIceServer`

### DataChannel open/close/reliability issues

- Primary files:
  - `sdk/objc/api/peerconnection/RTCDataChannel.mm`
  - `sdk/objc/api/peerconnection/RTCPeerConnection+DataChannel.mm`
  - `pc/data_channel_controller.cc`
  - `pc/sctp_data_channel.cc`
- Symbols:
  - `RTCDataChannel`
  - `DataChannelInterface`
  - `sctp_data_channel`

### Codec negotiation/encode/decode mismatch

- Primary files:
  - `media/engine/`
  - `sdk/objc/components/video_codec/RTCDefaultVideoEncoderFactory.m`
  - `sdk/objc/components/video_codec/RTCVideoEncoderH264.mm`
  - `sdk/objc/components/video_codec/RTCVideoDecoderH264.mm`
- Symbols:
  - `VideoEncoder`
  - `VideoDecoder`
  - `H264`
  - `VP8`
  - `VP9`
  - `AV1`

## Blast Radius Checklist

When proposing change impact, check:

- Obj-C wrapper plus underlying C++ owner path.
- Header/API contract under `api/` and wrapper converter files.
- PeerConnection/transport transitions under `pc/` and `p2p/base/`.
- Test candidates in `sdk/objc/unittests/`, `pc/*unittest*`, and related integration tests.
