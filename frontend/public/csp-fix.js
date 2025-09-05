/**
 * Content Security Policy Fix
 * Handles CSP violations and provides fallbacks
 */

// Override audio creation to handle CSP violations
const originalAudio = window.Audio;
window.Audio = function(src) {
  try {
    return new originalAudio(src);
  } catch (error) {
    console.warn('🔊 Audio creation blocked by CSP, using silent fallback');
    
    // Return a mock audio object that doesn't violate CSP
    return {
      play: () => Promise.resolve(),
      pause: () => {},
      load: () => {},
      currentTime: 0,
      duration: 0,
      volume: 1,
      muted: false,
      paused: true,
      ended: false,
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true
    };
  }
};

// Handle WebSocket CSP violations
const originalWebSocket = window.WebSocket;
window.WebSocket = function(url, protocols) {
  // Check if URL is allowed by CSP
  if (url.includes('echo.websocket.org')) {
    console.warn('🌐 WebSocket to external domain blocked by CSP, using fallback');
    
    // Return a mock WebSocket that doesn't violate CSP
    const mockWS = {
      readyState: 1, // OPEN
      send: (data) => console.log('Mock WebSocket send:', data),
      close: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null
    };
    
    // Simulate connection after a short delay
    setTimeout(() => {
      if (mockWS.onopen) mockWS.onopen({ type: 'open' });
    }, 100);
    
    return mockWS;
  }
  
  try {
    return new originalWebSocket(url, protocols);
  } catch (error) {
    console.error('WebSocket creation failed:', error);
    return mockWS;
  }
};

// Handle data: URI violations
function handleDataURIViolation(element, src) {
  console.warn('🔒 Data URI blocked by CSP:', src.substring(0, 50) + '...');
  
  // For audio elements, remove the src to prevent CSP violation
  if (element.tagName === 'AUDIO') {
    element.removeAttribute('src');
    element.muted = true;
  }
  
  // For images, use a placeholder
  if (element.tagName === 'IMG') {
    element.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMSIgaGVpZ2h0PSIxIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjwvc3ZnPg==';
  }
}

// Monitor for CSP violations
document.addEventListener('securitypolicyviolation', (e) => {
  console.warn('🔒 CSP Violation detected:', {
    directive: e.violatedDirective,
    blockedURI: e.blockedURI,
    originalPolicy: e.originalPolicy
  });
  
  // Handle specific violations
  if (e.violatedDirective.includes('media-src') && e.blockedURI.includes('data:audio')) {
    console.log('🔊 Audio data URI blocked - using silent mode');
  }
  
  if (e.violatedDirective.includes('connect-src') && e.blockedURI.includes('websocket')) {
    console.log('🌐 WebSocket connection blocked - using fallback');
  }
});

// Override setAttribute to catch data: URI assignments
const originalSetAttribute = Element.prototype.setAttribute;
Element.prototype.setAttribute = function(name, value) {
  if ((name === 'src' || name === 'href') && typeof value === 'string' && value.startsWith('data:')) {
    if (this.tagName === 'AUDIO' && value.includes('audio/')) {
      console.warn('🔊 Preventing CSP violation for audio data URI');
      return; // Don't set the attribute
    }
  }
  
  return originalSetAttribute.call(this, name, value);
};

console.log('✅ CSP violation handler loaded');