graph TD
    subgraph "Movie ID Processing"
        A[Movie ID Input] --> B[StringLookup Layer]
        B --> C[Embedding Layer<br/>32 dimensions]
    end

    subgraph "Genre Processing"
        D[Genre Preferences Input<br/>19 dimensions] --> E[Dense Layer<br/>64 neurons, ReLU]
        E --> F[Dense Layer<br/>32 dimensions]
    end

    subgraph "Combined Processing"
        C --> G[Concatenate]
        F --> G
        G --> H[Dense Layer<br/>32 neurons, ReLU]
        H --> I[Dense Layer<br/>16 neurons, ReLU]
        I --> J[Dense Layer<br/>1 neuron]
        J --> K[Final Rating Prediction]
    end

    style A fill:#f9f,stroke:#333
    style D fill:#f9f,stroke:#333
    style K fill:#9f9,stroke:#333