from __future__ import annotations

from datetime import datetime

from app.models.comment import Comment, ExtractionResult


def export_json(result: ExtractionResult) -> str:
    return result.model_dump_json(indent=2)


def export_markdown(result: ExtractionResult) -> str:
    lines = [
        f"# X Comment Extraction: {result.source_url}",
        "",
        f"- Extracted at: {_format_dt(result.extracted_at)}",
        f"- Total comments: {result.total_comments}",
        f"- Post author: @{result.post_author.username} ({result.post_author.display_name})",
        "",
        "## Post",
        "",
        result.post_text or "_No post text captured._",
        "",
        "## Comments",
        "",
    ]

    for comment in result.comments:
        lines.extend(_comment_to_markdown(comment, level=3))

    return "\n".join(lines).strip() + "\n"


def _comment_to_markdown(comment: Comment, level: int) -> list[str]:
    prefix = "#" * level
    lines = [
        f"{prefix} Comment #{comment.index}",
        "",
        f"- Author: [@{comment.author.username}](https://x.com/{comment.author.username}) — **{comment.author.display_name}**"
        + (" ✓ Verified" if comment.author.verified else ""),
        f"- Timestamp: {_format_dt(comment.timestamp)}",
        f"- Likes: {comment.like_count}",
        f"- Retweets: {comment.retweet_count}",
        f"- Replies: {comment.reply_count}",
        f"- Bookmarks: {comment.bookmark_count}",
        "",
        comment.text or "_No text captured._",
        "",
    ]

    if comment.mentions:
        lines.append(f"**Mentions:** {', '.join(f'[@{m}](https://x.com/{m})' for m in comment.mentions)}")
        lines.append("")

    if comment.hashtags:
        lines.append(f"**Hashtags:** {', '.join(f'#{tag}' for tag in comment.hashtags)}")
        lines.append("")

    if comment.emails:
        lines.append("**Emails found:**")
        lines.append("")
        for email in comment.emails:
            lines.append(f"- `{email}`")
        lines.append("")

    if comment.links:
        lines.append("**Links found in text:**")
        lines.append("")
        for link in comment.links:
            lines.append(f"- {link}")
        lines.append("")

    if comment.resources:
        lines.append("**Resources:**")
        lines.append("")
        for resource in comment.resources:
            lines.append(f"- `{resource.type}` {resource.url}")
        lines.append("")

    if comment.annotation:
        lines.extend(
            [
                "**Annotation**",
                "",
                f"- Sentiment: {comment.annotation.sentiment} ({comment.annotation.sentiment_score})",
                f"- Topics: {', '.join(comment.annotation.topics)}",
                f"- Language: {comment.annotation.language}",
                f"- Spam: {comment.annotation.is_spam}",
                f"- Summary: {comment.annotation.summary}",
                "",
            ]
        )

    for reply in comment.replies:
        lines.extend(_comment_to_markdown(reply, level=min(level + 1, 6)))

    return lines


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "unknown"
    return value.isoformat()
