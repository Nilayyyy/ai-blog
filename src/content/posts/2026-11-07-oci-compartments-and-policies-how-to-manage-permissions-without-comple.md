---
title: "OCI Compartments and Policies: How to Manage Permissions Without Complexity"
description: "Learn how to structure OCI compartments and IAM policies by focusing on resource hierarchy and access boundaries instead of manual permissions."
pubDate: 2026-11-07
tags: [oci, iam, cloud, infrastructure, access-control]
canonical:
---

Managing access in a cloud environment often feels like a sprawling mess of checkboxes and roles. In Oracle Cloud Infrastructure (OCI), the primary mechanism for organizing resources and controlling access is the Compartment. If you understand how compartments nest and how policies flow through them, you can build a secure environment without relying on trial-and-error configurations.

## The Hierarchical Mental Model

Think of compartments as a file system. Just as you might have a folder structure like `/Production/Database/Backup`, you create compartments to group related resources. A compartment is a logical container, not a physical one. You can move resources between compartments, but it is better to plan the structure early.

The hierarchy is the most important part of your model. Every child compartment inherits the policies of its parent. If you place a policy at the root compartment, it applies to every resource in every compartment beneath it. This is powerful for global governance, but dangerous if you are too broad. 

Keep your hierarchy shallow. A common pattern is to have a root compartment, followed by environment-level compartments (Dev, Staging, Prod), and then sub-compartments for specific workloads or teams. This structure allows you to apply restrictive policies at the top levels and more granular ones as you drill down into specific projects.

## The Policy Syntax Anatomy

OCI policies follow a declarative syntax: `Allow group <group_name> to <verb> <resource-type> in compartment <compartment_name>`.

*   **Group:** Do not write policies for individual users. Write them for groups. Assign users to groups and manage permissions through group membership.
*   **Verb:** These represent the level of access. `Inspect` is read-only for metadata. `Read` allows reading the resource and its data. `Use` allows updating or modifying existing resources. `Manage` grants full control, including deleting resources or changing policies.
*   **Resource-type:** This is the specific service component, such as `instance-family`, `bucket`, or `autonomous-database`.
*   **Compartment:** This defines the scope.

If you want a team to manage instances in the Dev compartment, your policy looks like this:

`Allow group DevTeam to manage instance-family in compartment Dev`

This is direct and explicit. Avoid adding unnecessary complexity until you have a requirement that the base syntax cannot handle.

## Defining Permissions by Role

Avoid the temptation to assign `Manage` permissions to everyone. It is the easiest way to accidentally delete a production database or expose an object storage bucket. Map your policies to the actual job function.

*   **Viewers:** Use `Allow group <group> to inspect <resource-family> in compartment <comp>`. This allows users to see that a resource exists without being able to see sensitive details or modify the configuration.
*   **Operators:** Use `Allow group <group> to use <resource-family> in compartment <comp>`. This is perfect for DevOps engineers who need to restart instances or update configurations but should not be creating or terminating infrastructure.
*   **Administrators:** Only grant `manage` access to the specific compartments where users are responsible for the entire lifecycle of the resources. 

By defining these roles, you prevent "permission creep," where users accumulate access levels they no longer need. If a team says they cannot get their work done, check if you have missed a specific resource type. Sometimes `instance-family` is not enough if they also need to manage the associated `volume-family` or `virtual-network-family`.

## Inheritance and Scope

Policies are additive. If a user is a member of two groups, they get the union of the permissions of both groups. If you have a policy at the root level that grants `read` access and a policy at a child level that grants `manage` access, the user has both.

Least privilege starts at the root. Minimize the number of policies defined at the tenancy root. Use the root compartment only for policies that must apply globally, such as allowing an audit group to inspect all resources across the entire tenancy. For everything else, attach the policy to the lowest possible level in the compartment tree. 

If you define a policy in the compartment where the resource lives, you limit the "blast radius." If that policy is misconfigured, it only affects that specific compartment, not the entire cloud account.

## Troubleshooting Access

When a user reports they cannot perform an action, verify the policy evaluation logic. OCI uses an "allow-only" system; if no policy explicitly allows the action, it is denied by default. <!-- VERIFY: check for specific OCI policy evaluation logic -->

Start your debugging process with these three checks:
1.  **Is the user in the right group?** Check the Identity and Access Management (IAM) console to confirm group membership.
2.  **Does the policy cover the resource?** Ensure the `resource-type` matches the task. If the user is trying to attach a volume, they need `use` permissions on both the `instance-family` and the `volume-family`. 
3.  **Is there a conflict?** Check if a broader policy is being overridden or if a specific `where` clause is restricting access.

If you are still stuck, look at the audit logs. OCI logs provide information on why an API call was rejected. It often points directly to the lack of authorization for a specific verb and resource type. Do not guess which policy is failing; look at the logs to see exactly what the system expected and what it received. If you are consistently hitting issues, simplify the policy to the absolute minimum, verify it works, and then add constraints back one by one.

## My take

TODO(nilay): add 2-4 sentences from your own experience or opinion, then delete this line.

