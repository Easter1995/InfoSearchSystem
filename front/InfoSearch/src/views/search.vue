<script setup lang="ts">
import { getInfo, subRate } from '@/api/search';
import { SearchResult } from '@/typings/searchType';
import { Search } from '@element-plus/icons-vue'
import { ElLoading, ElNotification } from 'element-plus';
import { nextTick, ref } from 'vue';
import { stemmer } from 'stemmer'

const userInput = ref('')
const userRate = ref(0)
const isFirstSearch = ref(true)
const showContent = ref(false)
const showRate = ref(false)
const searchList = ref<SearchResult>({
    results: [],
    timestamp: '',
    total: 0
})

enum textType {
    DIR = 0,
    WRI,
    STAR,
    TITLE,
    SUM
}

const highlight = (text: string, match: string, type: number) => {
  if (!text || !match) return text

  const stemmedMatch = stemmer(match.toLowerCase()).trim()

  return text.replace(/\b\w+\b/g, (word) => {
    const stemmedWord = stemmer(word.toLowerCase())
    if (stemmedWord === stemmedMatch) {
      return `<span class="highlight">${word}</span>`
    }
    return word
  })
}

const handleSearch = async () => {
    if (!userInput.value) return
    if (isFirstSearch.value) {
        isFirstSearch.value = false
        await nextTick()
    }

    const loading = ElLoading.service({
        lock: true,
        text: 'Loading',
        background: 'rgba(0, 0, 0, 0.7)',
    })
    const res = await getInfo(userInput.value)
    loading.close()
    // console.log(res)
    if (res.total === 0) {
        ElNotification({
            type: 'error',
            message: 'no content matches'
        })
        return
    }
    showContent.value = true
    showRate.value = true
    searchList.value = res
}

const handleRate = async (val: number) => {
    userRate.value = val
    const res = await subRate(userInput.value, userRate.value)
    if (res.success) {
        ElNotification({
            type: 'success',
            message: res.message
        })
    } else {
        ElNotification({
            type: 'error',
            message: '出错了'
        })
    }
    userRate.value = 0
    showRate.value = false
}
</script>

<template>
    <div class="main">
        <div class="container">
            <div class="search-box">
                <el-input v-model="userInput" style="width: 600px; height: 70px;" placeholder="Type something"
                    :prefix-icon="Search" @keyup.enter="handleSearch" />
            </div>
            <div class="rate" v-if="showRate">
                <el-rate v-model="userRate" @change="handleRate" size="large" allow-half />
            </div>
            <div class="search-body">
                <ul class="search-list" style="list-style: none;">
                    <li class="search-content" v-for="(item, index) in searchList.results" :key="index">
                        <div class="info">
                            Similarity: {{ item.sim }} Target: {{ item.match }}
                        </div>
                        <el-divider></el-divider>
                        <div class="title" v-html="highlight(item.title, item.match, textType.TITLE)"></div>
                        <div class="info">rate: {{ item.rate }}</div>
                        <div class="info">
                            <span>Director: </span>
                            <span class="info" v-html="highlight(item.director, item.match, textType.DIR)"></span>
                        </div>
                        <div class="info">
                            <span>Writers: </span>
                            <span class="info" v-html="highlight(item.writers, item.match, textType.WRI)"></span>
                        </div>
                        <div class="info">
                            <span>Stars: </span>
                            <span class="info" v-html="highlight(item.stars, item.match, textType.STAR)"></span>
                        </div>
                        <div class="summary" v-html="highlight(item.summary, item.match, textType.SUM)"></div>
                        <el-divider></el-divider>
                        <div class="info">Search Timestamp: {{ searchList.timestamp }}</div>
                        <div class="info">Count: {{ index + 1 }} / {{ searchList.total }} </div>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.main {
    min-height: 100vh;
    background-image: linear-gradient(120deg, #e0c3fc 0%, #8ec5fc 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    .rate {
        z-index: 100;
        right: 10px;
        bottom: 30px;
        height: 50px;
        padding: 9px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        position: fixed;
        background-image: linear-gradient(to top, #a8edea 0%, #fed6e3 100%);
        border-radius: 20px;
    }

    .container {
        padding: 30px;
        
        .search-box {
            text-align: center;
            margin-bottom: 30px;
        }

        .search-body {
            padding: 0 40px 0 40px;

            .search-content {
                padding: 30px;
                margin-bottom: 20px;
                border-radius: 20px;
                color: #606266;
                background-color: rgb(255, 255, 255);
                box-shadow: 0px 3px 10px rgb(149, 149, 149);

                .info {
                    font-size: 14px;
                }
                .title {
                    font-weight: bolder;
                    margin-bottom: 10px;
                }
                .summary {
                    margin-top: 10px;
                    font-size: small;
                }
            }
        }
    }
}

::v-deep .highlight {
    background-color: rgb(255, 209, 238);
    font-weight: bold;
}

::v-deep .el-input__wrapper {
    border-radius: 33px;
    box-shadow: 0px 3px 10px rgb(149, 149, 149);

    .el-input__prefix {
        font-size: 18px;
    }

    .el-input__inner {
        font-size: 18px;
    }
}
</style>