module.exports = {
    plugins: [
        "@semantic-release/commit-analyzer",
        "@semantic-release/release-notes-generator",
        [
            "@semantic-release/changelog",
            {
                changelogTitle: `# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [In Progress](https://github.com/tophat/syrupy/pulls)

See open [issues](https://github.com/tophat/syrupy/issues)

## [Unreleased](https://github.com/tophat/syrupy/releases)

See closed [issues](https://github.com/tophat/syrupy/pulls?q=is%3Apr+is%3Amerged+sort%3Acreated-desc+-label%3Areleased)`,
            },
        ],
        ["@semantic-release/git", { assets: ["CHANGELOG.md"] }],
        "@semantic-release/github",
    ],
};
