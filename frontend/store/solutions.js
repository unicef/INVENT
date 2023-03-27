const cleanState = () => ({
  allSolutionsList: {},
})

export const state = () => ({
  ...cleanState(),
})

export const getters = {
  getSolutionsList: (state) => state.allSolutionsList.solutions,
}

export const actions = {
  async loadSolutionsList({ state, commit, dispatch, rootGetters }, id) {
    const response = await this.$axios.get(`/api/portfolio/${id}`)
    commit('PUT_SOLUTION_LIST', response.data)
  },
}

export const mutations = {
  PUT_SOLUTION_LIST: (state, data) => {
    state.allSolutionsList = data
  },
}
