export interface SearchInfo {
    director: string,
    match: string,
    rate: string,
    sim: number,
    stars: string,
    summary: string,
    title: string,
    url: string,
    writers: string
}

export interface SearchResult {
    corrections: Array<string>,
    has_corrections: Boolean,
    results: Array<SearchInfo>,
    timestamp: string,
    total: number
}