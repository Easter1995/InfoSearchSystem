import { SearchResult } from '@/typings/searchType';
import axios from 'axios'

export async function getInfo(q: string): Promise<SearchResult> {
    const res = await axios.get<SearchResult>('/api/search', {
        params: { q }
    })
    return res.data
}

export async function subRate(query: string, rate: number) {
    const res = await axios.post('/api/rate', {
        query,
        rate
    })
    return res.data
}