from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class OperatingConditionNormalizer:
    def __init__(self, n_clusters=4, random_state=42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = None
        self.scalers_per_mode = {}
        self.op_cols = ['op1', 'op2', 'op3']

    def fit(self, df):
        op = df[self.op_cols].values
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state).fit(op)
        df_local = df.copy()
        df_local['op_mode'] = self.kmeans.predict(op)
        sensor_cols = [c for c in df_local.columns if c.startswith('sensor_')]
        for mode in range(self.n_clusters):
            mode_data = df_local[df_local.op_mode == mode][sensor_cols]
            scaler = StandardScaler()
            if len(mode_data):
                scaler.fit(mode_data)
            self.scalers_per_mode[mode] = scaler
        return self

    def transform(self, df):
        if self.kmeans is None:
            raise RuntimeError("Call fit() before transform()")
        df_local = df.copy()
        df_local['op_mode'] = self.kmeans.predict(df_local[self.op_cols].values)
        sensor_cols = [c for c in df_local.columns if c.startswith('sensor_')]
        df_local[sensor_cols] = df_local[sensor_cols].astype(float)
        for mode, scaler in self.scalers_per_mode.items():
            mask = df_local.op_mode == mode
            if mask.sum() > 0:
                mode_slice = df_local.loc[mask, sensor_cols].astype(float)
                df_local.loc[mask, sensor_cols] = scaler.transform(mode_slice)
        return df_local

    def fit_transform(self, df):
        return self.fit(df).transform(df)
