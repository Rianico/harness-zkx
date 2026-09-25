export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    // PR bodies become squash-merge commit bodies and are written for humans
    // on GitHub; wrapping them to 100 cols hurts readability for zero release
    // value (semantic-release only parses the title). Title rules stay enforced.
    "body-max-line-length": [0],
  },
};
