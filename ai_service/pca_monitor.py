import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

class PCAMonitor:
    def __init__(self, n_components: int = 3):
        self.n_components = n_components
        self.pca = PCA(n_components=n_components)
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def fit(self, data: np.ndarray):
        """Fit PCA model"""
        scaled_data = self.scaler.fit_transform(data)
        self.pca.fit(scaled_data)
        self.is_fitted = True
        
    def monitor(self, data: np.ndarray):
        """Monitor new data points"""
        if not self.is_fitted:
            return 0.0, 0.0
            
        scaled_data = self.scaler.transform(data)
        transformed = self.pca.transform(scaled_data)
        
        # T² statistic
        t2 = np.sum(transformed**2, axis=1)
        
        # SPE statistic
        reconstructed = self.pca.inverse_transform(transformed)
        spe = np.sum((scaled_data - reconstructed)**2, axis=1)
        
        return float(t2[0]), float(spe[0])