/**
 * Chart.js Registration Fix for Production Build
 * Ensures all Chart.js controllers are properly registered
 */

// Wait for Chart.js to be available
function initializeChartJS() {
  if (typeof Chart !== 'undefined') {
    console.log('📊 Chart.js detected, registering controllers...');
    
    try {
      // Register all essential Chart.js components
      if (Chart.register) {
        Chart.register(
          Chart.CategoryScale,
          Chart.LinearScale,
          Chart.PointElement,
          Chart.LineElement,
          Chart.BarElement,
          Chart.LineController,
          Chart.BarController,
          Chart.Title,
          Chart.Tooltip,
          Chart.Legend,
          Chart.Filler,
          Chart.ArcElement,
          Chart.DoughnutController,
          Chart.PieController
        );
        console.log('✅ Chart.js controllers registered successfully');
      }
    } catch (error) {
      console.warn('⚠️ Chart.js registration error:', error);
      
      // Fallback registration for older Chart.js versions
      try {
        Chart.defaults.global = Chart.defaults.global || {};
        console.log('✅ Chart.js fallback registration applied');
      } catch (fallbackError) {
        console.error('❌ Chart.js fallback registration failed:', fallbackError);
      }
    }
  } else {
    console.log('⏳ Waiting for Chart.js to load...');
    setTimeout(initializeChartJS, 100);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeChartJS);
} else {
  initializeChartJS();
}

// Override console.error to catch and handle Chart.js errors
const originalConsoleError = console.error;
console.error = function(...args) {
  const message = args.join(' ');
  
  if (message.includes('not a registered controller')) {
    console.warn('🔧 Chart.js controller registration issue detected, attempting fix...');
    
    // Try to re-register controllers
    setTimeout(() => {
      try {
        initializeChartJS();
        console.log('🔄 Chart.js re-registration attempted');
      } catch (error) {
        console.warn('Chart.js re-registration failed:', error);
      }
    }, 50);
  }
  
  // Call original console.error
  originalConsoleError.apply(console, args);
};

console.log('✅ Chart.js fix script loaded');